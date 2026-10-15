from pathlib import Path
import subprocess, tempfile
root = Path(__file__).resolve().parents[1]
checks = r'''
import Cocoa
func check(_ value: @autoclosure () -> Bool, _ name: String) { if !value() { fatalError(name) }; print("PASS: " + name) }
func marker(_ source: String, _ caret: Int) -> String? {
    guard let range = MarkdownStyle.taskMarker(at: caret, in: source) else { return nil }
    return (source as NSString).substring(with: range)
}

// Line offsets: L1 "- [ ] Buy apples" at 0, L2 "- [x] Post letter" at 17, L3 "plain line" at 35,
// L4 "  - [ ] Indented" at 46, L5 "* [X] Star item" at 63, L6 "+ [ ] Plus item" at 79, L7 "- [x]" at 95.
let doc = "- [ ] Buy apples\n- [x] Post letter\nplain line\n  - [ ] Indented\n* [X] Star item\n+ [ ] Plus item\n- [x]"
check(marker(doc, 3) == "[ ]", "marker found inside brackets")
check(marker(doc, 8) == "[ ]", "marker found from task body")
check(marker(doc, 0) == "[ ]", "marker found from line start bullet")
check(MarkdownStyle.taskMarker(at: 3, in: doc)?.length == 3, "marker range covers the three checkbox characters")
check(marker(doc, 20) == "[x]", "done marker on second line")
check(marker(doc, 50) == "[ ]", "indented task marker")
check(marker(doc, 66) == "[X]", "uppercase X marker on star bullet")
check(marker(doc, 81) == "[ ]", "plus bullet task")
check(marker(doc, 99) == "[x]", "bare done marker without title")
check(marker(doc, 100) == "[x]", "caret at end of document")

check(marker(doc, 38) == nil, "plain line has no marker")
let numbered = "1. [ ] not a task"
check(marker(numbered, 5) == nil, "ordered list is not a task")
let plainList = "- plain item"
check(marker(plainList, 4) == nil, "plain bullet is not a task")
let fenced = "```\n- [ ] literal\n```"
check(marker(fenced, 8) == nil, "closed fence blocks toggling")
let openFence = "```\n- [ ] literal"
check(marker(openFence, 8) == nil, "open fence blocks toggling")
let afterFence = "```\ncode\n```\n- [ ] after"
check(marker(afterFence, 20) == "[ ]", "task after a closed fence still toggles")
check(marker("", 0) == nil, "empty note has no marker")
check(MarkdownStyle.taskMarker(at: -1, in: doc) == nil, "caret before the document")
check(MarkdownStyle.taskMarker(at: 9999, in: doc) == nil, "caret beyond the document")

check(MarkdownStyle.toggledMarker(" ") == "x", "space toggles to x")
check(MarkdownStyle.toggledMarker("x") == " ", "x toggles to space")
check(MarkdownStyle.toggledMarker("X") == " ", "X toggles to space")
check(MarkdownStyle.toggledMarker("a") == nil, "other characters do not toggle")
var text = doc as NSString
let task = MarkdownStyle.taskMarker(at: 3, in: doc)!
let replacement = MarkdownStyle.toggledMarker(text.substring(with: NSRange(location: task.location + 1, length: 1)).first!)!
let toggled = text.replacingCharacters(in: NSRange(location: task.location + 1, length: 1), with: String(replacement))
check(marker(toggled, 3) == "[x]", "toggle round trip marks the task done")

let progress = MarkdownStyle.taskProgress(doc)!
check(progress.done == 3 && progress.total == 6, "progress counts six tasks with three done")
check(MarkdownStyle.taskProgress(toggled)!.done == 4, "toggling updates the done count")
check(MarkdownStyle.taskProgress("no tasks here") == nil, "plain note has no progress")
check(MarkdownStyle.taskProgress("1. [ ] a\n- item") == nil, "non-bullet checkboxes are ignored")
let fencedTask = "```\n- [ ] hidden\n```\n- [x] visible"
let fencedProgress = MarkdownStyle.taskProgress(fencedTask)!
check(fencedProgress.done == 1 && fencedProgress.total == 1, "fenced tasks are not counted")

let unicode = "😀\n- [ ] 中文任务"
check(marker(unicode, 5) == "[ ]", "UTF-16 offsets handle emoji")
check(marker(unicode, 3) == "[ ]", "marker found from bullet before CJK body")

// The checkbox must stay full-size and tinted on inactive lines so it remains clickable.
let styled = NSTextStorage(string: "- [ ] 待办\n正文\n")
let baseFont = NSFont.systemFont(ofSize: 17)
MarkdownStyle.apply(styled, selection: NSRange(location: styled.length, length: 0), font: baseFont, enabled: true)
check(styled.string == "- [ ] 待办\n正文\n", "styling preserves the exact source")
check((styled.attribute(.font, at: 2, effectiveRange: nil) as! NSFont).pointSize == 17, "inactive task marker stays visible")
check((styled.attribute(.foregroundColor, at: 2, effectiveRange: nil) as! NSColor) == NSColor.black.withAlphaComponent(0.45), "task marker is tinted as a control")
check((styled.attribute(.font, at: 7, effectiveRange: nil) as! NSFont).pointSize == 17, "task body keeps the base font")
MarkdownStyle.apply(styled, selection: NSRange(location: 2, length: 0), font: baseFont, enabled: true)
check((styled.attribute(.font, at: 2, effectiveRange: nil) as! NSFont).pointSize == 17, "active task marker stays visible too")
'''
with tempfile.TemporaryDirectory(prefix='string-notes-tasks-') as folder:
    path = Path(folder)
    (path / 'main.swift').write_text(checks)
    subprocess.run(['xcrun','swiftc','-module-cache-path','/tmp/string-notes-module-cache',str(root/'Sources/Localization.swift'),str(root/'Sources/Markdown.swift'),str(path/'main.swift'),'-o',str(path/'test')],check=True)
    subprocess.run([str(path/'test')],check=True)
