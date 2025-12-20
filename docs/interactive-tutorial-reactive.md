# Interactive Tutorial (Enhanced Reactivity)

Experience Skillet with **enhanced reactive behaviors**: contextual hints, error detection, and progress celebrations.

<ClientOnly>
  <skillet-reactive-docs height="700px"></skillet-reactive-docs>
  <skillet-hint-toast></skillet-hint-toast>
  <skillet-celebration-overlay></skillet-celebration-overlay>
</ClientOnly>

## Reactive Features

This tutorial demonstrates the following reactive behaviors:

### Contextual Hints

The docs panel watches for patterns in the terminal output and shows helpful suggestions:

- **Error Detection**: Common errors (npm, git, Node.js) trigger hint toasts with fix suggestions
- **Help Suggestions**: When you run `--help` commands, hints provide additional context
- **Action Buttons**: Some hints include quick-action buttons to execute suggested commands

### Progress Celebration

- **Step Completion**: Subtle toast notifications when you complete each step
- **Tutorial Completion**: Full-screen celebration with confetti when you finish

### Try It Out

1. Complete the tutorial steps normally to see step completion toasts
2. Try running an invalid command to see error hints
3. Complete all steps to trigger the full celebration!

::: tip WebContainer Support
The interactive terminal requires a modern browser with WebContainer support (Chrome, Edge, or Firefox).
:::
