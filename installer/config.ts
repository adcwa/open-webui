export const packageConfig = {
  name: "open-webui",
  version: "0.4.7", // 与 package.json 保持一致
  description: "Open WebUI Client Application",
  author: "Open WebUI Team",
  
  // 应用配置
  app: {
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600
  },
  
  // 打包配置
  build: {
    appId: "com.open-webui.app",
    productName: "Open WebUI",
    copyright: "Copyright © 2024"
  }
}; 