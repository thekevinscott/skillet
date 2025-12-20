# Interactive Tutorial

<script setup>
// Single terminal instance persists as you scroll
</script>

<style>
.tutorial-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  margin: 32px 0;
  align-items: start;
}

.tutorial-prose {
  /* Scrolls naturally */
}

.tutorial-terminal {
  position: sticky;
  top: calc(var(--vp-nav-height, 64px) + 24px);
  height: calc(100vh - var(--vp-nav-height, 64px) - 48px);
}

.terminal-container {
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--vp-c-border);
  display: flex;
  flex-direction: column;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #252525;
  border-bottom: 1px solid #333;
}

.terminal-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.terminal-dot.red { background: #ff5f56; }
.terminal-dot.yellow { background: #ffbd2e; }
.terminal-dot.green { background: #27c93f; }

.terminal-title {
  flex: 1;
  text-align: center;
  font-size: 12px;
  color: #888;
  font-family: var(--vp-font-family-mono);
}

.terminal-body {
  flex: 1;
  min-height: 0;
}

@media (max-width: 960px) {
  .tutorial-layout {
    grid-template-columns: 1fr;
  }
  .tutorial-terminal {
    position: relative;
    top: 0;
    height: 400px;
    margin-bottom: 32px;
  }
}
</style>

<div class="tutorial-layout">
<div class="tutorial-prose">

Learn Skillet by doing. The terminal on the right stays visible as you scroll through each section. Try the commands as you go!

::: tip
The terminal is a fully sandboxed WebContainer environment running in your browser.
:::

---

## 1. Hello World

Let's start with a simple command to see how the terminal works.

Copy and run this command:

```bash
echo "Hello from Skillet!"
```

The terminal accepts any shell command. Try experimenting!

---

## 2. Explore Files

The terminal comes pre-loaded with some example files. List them:

```bash
ls -la
```

You should see:
- `hello.txt` - A simple text file
- `greeting.js` - A JavaScript file

---

## 3. Read File Contents

Read the contents of a file using `cat`:

```bash
cat hello.txt
```

You should see "Hello, World!" printed to the terminal.

---

## 4. Run JavaScript

The terminal has Node.js available. Run the greeting script:

```bash
node greeting.js
```

This prints "Welcome to Skillet!" to the console.

You can also run inline JavaScript:

```bash
node -e "console.log(2 + 2)"
```

---

## 5. Create New Files

Create a new file using echo with redirection:

```bash
echo "My new content" > myfile.txt
```

Verify it was created:

```bash
cat myfile.txt
```

---

## 6. Package Management

npm is available too. Initialize a project:

```bash
npm init -y
```

Then install a package:

```bash
npm install cowsay
```

And use it:

```bash
npx cowsay "Skillet is awesome!"
```

---

## Next Steps

You've learned the basics! Here's what's next:

- **[Getting Started](/getting-started)** - Set up Skillet in your project
- **[GitHub](https://github.com/thekevinscott/skillet)** - Browse the source code

</div>
<div class="tutorial-terminal">
<div class="terminal-container">
<div class="terminal-header">
<span class="terminal-dot red"></span>
<span class="terminal-dot yellow"></span>
<span class="terminal-dot green"></span>
<span class="terminal-title">Terminal — WebContainer</span>
</div>
<div class="terminal-body">
<ClientOnly>
<skillet-terminal
  height="100%"
  :files='{"hello.txt": "Hello, World!", "greeting.js": "console.log(\"Welcome to Skillet!\");"}'
></skillet-terminal>
</ClientOnly>
</div>
</div>
</div>
</div>
