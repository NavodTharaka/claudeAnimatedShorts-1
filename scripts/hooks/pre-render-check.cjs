// PreToolUse hook: before any `remotion render` Bash command, run the project
// typecheck (`npm run tsc`). If it fails, exit 2 so Claude Code blocks the call
// and shows the errors. Any other command passes through untouched.
const { spawnSync } = require("child_process");
const path = require("path");

let input = "";
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
  let command = "";
  try {
    command = JSON.parse(input).tool_input?.command ?? "";
  } catch {
    process.exit(0); // not a tool call we understand; do not block
  }
  if (!/remotion\s+render/.test(command)) process.exit(0);

  const projectDir = process.env.CLAUDE_PROJECT_DIR || path.resolve(__dirname, "../..");
  const run = spawnSync("npm", ["run", "tsc", "--silent"], {
    cwd: projectDir,
    encoding: "utf8",
    shell: process.platform === "win32",
  });
  if (run.status === 0) process.exit(0);

  const output = (run.stdout || "") + (run.stderr || "");
  process.stderr.write(
    "Render blocked: `npm run tsc` failed. Fix these type errors first " +
      "(scratch .ts files inside out/ break tsc; rename them .txt):\n" +
      output.slice(0, 4000)
  );
  process.exit(2);
});
