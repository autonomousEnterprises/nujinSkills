import * as fs from "fs";
import * as path from "path";

/**
 * Strategy Validator for Hummingbot.
 * Scans Python strategy scripts to detect structural deficiencies, logic issues, and risk flags.
 * 
 * Usage:
 *   npx tsx validate.ts --file skills/hummingbot-strategy/generated/mystratey.py
 */

function parseArgs() {
  const args = process.argv.slice(2);
  const options: Record<string, string> = {
    file: "",
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--file" && args[i + 1]) {
      options.file = args[i + 1];
      break;
    }
  }

  return options;
}

const opts = parseArgs();

if (!opts.file) {
  console.error("Usage: npx tsx validate.ts --file <path/to/strategy.py>");
  process.exit(1);
}

const filePath = path.isAbsolute(opts.file) ? opts.file : path.join(process.cwd(), opts.file);

if (!fs.existsSync(filePath)) {
  console.error(`Error: File does not exist at ${filePath}`);
  process.exit(1);
}

const content = fs.readFileSync(filePath, "utf8");
const lines = content.split("\n");

interface RuleResult {
  type: "ERROR" | "WARNING" | "INFO";
  message: string;
  line?: number;
}

const results: RuleResult[] = [];

// Rule 1: Inheritance Check
const inheritsScript = /class\s+\w+\(ScriptStrategyBase\):/.test(content);
const inheritsController = /class\s+\w+\(ControllerBase\):/.test(content);

if (!inheritsScript && !inheritsController) {
  results.push({
    type: "ERROR",
    message: "Strategy class must inherit from either ScriptStrategyBase or ControllerBase.",
  });
}

// Rule 2: Basic Method Check
if (inheritsScript) {
  if (!content.includes("def on_tick")) {
    results.push({
      type: "ERROR",
      message: "Legacy ScriptStrategyBase strategy must implement the 'on_tick' callback method.",
    });
  }
  const hasMarkets = /markets\s*(:\s*[^=]+)?=/.test(content);
  if (!hasMarkets) {
    results.push({
      type: "ERROR",
      message: "Legacy ScriptStrategyBase strategy must define the 'markets' configuration variable.",
    });
  }
}

if (inheritsController) {
  if (!content.includes("def determine_executor_actions")) {
    results.push({
      type: "ERROR",
      message: "Strategy V2 ControllerBase controller must implement the 'determine_executor_actions' method.",
    });
  }
  if (!content.includes("def update_processed_data")) {
    results.push({
      type: "WARNING",
      message: "Strategy V2 ControllerBase controller should implement the 'update_processed_data' method to calculate indicators.",
    });
  }
}

// Rule 3: Float precision check
// Warns about assignments like: order_amount = 0.01 instead of Decimal("0.01")
for (let i = 0; i < lines.length; i++) {
  const line = lines[i].trim();
  
  // Skip comments
  if (line.startsWith("#")) continue;

  // Look for float assignments (e.g. order_amount = 0.05)
  const floatMatch = /^\w+\s*=\s*(?:[0-9]*\.[0-9]+|[0-9]+\.[0-9]*)(?!\d)(?!\s*#\s*type)(?!\s*,\s*Decimal)/.exec(line);
  if (floatMatch && !line.includes("Decimal")) {
    const varName = floatMatch[0].split("=")[0].trim();
    const isIndicatorParam = /rsi|period|length|window|level|boundary|threshold|count/i.test(varName);
    if (!isIndicatorParam) {
      results.push({
        type: "WARNING",
        message: `Possible floating-point value assigned directly. Use Decimal wrapping: Decimal("${floatMatch[0].split("=")[1].trim()}")`,
        line: i + 1,
      });
    }
  }
  
  // Check if float conversion function is called directly instead of using Decimal
  if (line.includes("float(") && !line.includes("pandas") && !line.includes("numpy") && !line.includes("rsi") && !line.includes("iloc") && !line.includes("df") && !line.includes("candles")) {
    results.push({
      type: "WARNING",
      message: "Using raw float(...) type casting. Prefer converting rates and values directly into Decimal characters for precision.",
      line: i + 1,
    });
  }
}

// Rule 4: Order Flooding Check (for ScriptStrategyBase only)
if (inheritsScript) {
  const containsBuySell = /self\.(buy|sell)\(/.test(content);
  const checksActiveOrders = /active_order_ids|self\.active_orders|order_placed|self\.order_placed|self\.last_trade_timestamp|current_position|self\.current_position/.test(content);
  
  if (containsBuySell && !checksActiveOrders) {
    results.push({
      type: "ERROR",
      message: "Strategy places buy or sell orders but does not appear to check for active orders or last trade timestamps. This will cause order flooding in the 1-second tick loop.",
    });
  }
}

// Rule 5: format_status / status report check
if (!content.includes("def format_status") && !content.includes("def determine_status_text")) {
  results.push({
    type: "INFO",
    message: "No custom status text formatter found. Implementing format_status() (ScriptStrategyBase) or determine_status_text() (ControllerBase) provides better console metrics.",
  });
}

// Print results
console.log("══════════════════════════════════════════════════════════════════════");
console.log(`  🔍 Hummingbot Strategy Validation Report`);
console.log(`  File: ${opts.file}`);
console.log("══════════════════════════════════════════════════════════════════════");

const errors = results.filter((r) => r.type === "ERROR");
const warnings = results.filter((r) => r.type === "WARNING");
const infos = results.filter((r) => r.type === "INFO");

if (results.length === 0) {
  console.log("  ✅ Strategy passed all validation checks! No issues found.");
} else {
  if (errors.length > 0) {
    console.log(`  ❌ FAIL: ${errors.length} Critical errors found:`);
    errors.forEach((e) => {
      console.log(`    - [ERROR] ${e.message}${e.line ? ` (Line ${e.line})` : ""}`);
    });
  } else {
    console.log("  ⚠️  PASS with warnings:");
  }

  if (warnings.length > 0) {
    console.log(`\n  ⚠️  ${warnings.length} Warnings to address:`);
    warnings.forEach((w) => {
      console.log(`    - [WARN]  ${w.message}${w.line ? ` (Line ${w.line})` : ""}`);
    });
  }

  if (infos.length > 0) {
    console.log(`\n  ℹ️  ${infos.length} Information notes:`);
    infos.forEach((info) => {
      console.log(`    - [INFO]  ${info.message}${info.line ? ` (Line ${info.line})` : ""}`);
    });
  }
}

console.log("══════════════════════════════════════════════════════════════════════");

// Exit code based on error presence
process.exit(errors.length > 0 ? 1 : 0);
