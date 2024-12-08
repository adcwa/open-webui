import { build, Platform } from 'electron-builder';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function buildInstaller() {
  const platform = process.argv.find(arg => arg.startsWith('--platform='))?.split('=')[1] || 'all';
  
  try {
    if (platform === 'win' || platform === 'all') {
      await build({
        targets: Platform.WINDOWS.createTarget()
      });
    }

    if (platform === 'mac' || platform === 'all') {
      await build({
        targets: Platform.MAC.createTarget()
      });
    }
  } catch (error) {
    console.error('Error building installer:', error);
    process.exit(1);
  }
}

buildInstaller(); 