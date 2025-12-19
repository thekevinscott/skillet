import type { Tutorial } from '../types';

/**
 * A simple "Hello World" tutorial for testing the reactive docs system.
 */
export const helloWorldTutorial: Tutorial = {
  id: 'hello-world',
  name: 'Hello World',
  description: 'A simple introduction to the reactive docs system.',
  files: {
    'hello.txt': 'Hello, World!',
    'greeting.js': 'console.log("Welcome to Skillet!");',
  },
  steps: [
    {
      id: 'intro',
      title: 'Welcome to Skillet',
      description:
        "Let's explore the reactive docs system. We'll run some simple commands to see how it works.",
      command: 'echo "Hello from the terminal!"',
      showMeLabel: 'Show me',
      runningLabel: 'Running...',
    },
    {
      id: 'list-files',
      title: 'See your files',
      description:
        "We've pre-loaded some files in the terminal. Let's see what's here.",
      command: 'ls -la',
      showMeLabel: 'List files',
      runningLabel: 'Listing...',
    },
    {
      id: 'read-file',
      title: 'Read a file',
      description: "Now let's read the contents of hello.txt.",
      command: 'cat hello.txt',
      showMeLabel: 'Read file',
      runningLabel: 'Reading...',
      watchPattern: /Hello, World!/,
    },
    {
      id: 'run-script',
      title: 'Run a script',
      description: "Let's run the greeting.js script to see JavaScript in action.",
      command: 'node greeting.js',
      showMeLabel: 'Run script',
      runningLabel: 'Running...',
      watchPattern: /Welcome to Skillet!/,
    },
    {
      id: 'complete',
      title: 'Great job!',
      description:
        "You've completed the Hello World tutorial! You now know how the reactive docs system works.",
      command: 'echo "Tutorial complete! 🎉"',
      showMeLabel: 'Finish',
    },
  ],
};

export default helloWorldTutorial;
