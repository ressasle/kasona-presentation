import { AuthManager } from "C:/Users/Administrator/AppData/Roaming/npm/node_modules/notebooklm-mcp/dist/auth/auth-manager.js";
import { CONFIG } from "C:/Users/Administrator/AppData/Roaming/npm/node_modules/notebooklm-mcp/dist/config.js";

async function run() {
    console.log("\n╔══════════════════════════════════════════════════════════╗");
    console.error("║                                                          ║");
    console.error("║           NotebookLM Authentication Trigger              ║");
    console.error("║                                                          ║");
    console.error("╚══════════════════════════════════════════════════════════╝\n");
    
    console.log("🚀 Starting NotebookLM authentication trigger...");
    
    // Force show browser for interactive login
    CONFIG.headless = false;
    
    const authManager = new AuthManager();
    console.log("🌐 Opening browser for Google login...");
    
    const success = await authManager.performSetup((msg) => {
        console.log(`  📊 ${msg}`);
    }, true);
    
    if (success) {
        console.log("\n✅ [SUCCESS] Successfully logged in to NotebookLM!");
    } else {
        console.log("\n❌ [FAILED] Authentication failed or was cancelled.");
    }
    
    process.exit(success ? 0 : 1);
}

run().catch(err => {
    console.error("\n💥 [ERROR] Error during authentication:", err);
    process.exit(1);
});
