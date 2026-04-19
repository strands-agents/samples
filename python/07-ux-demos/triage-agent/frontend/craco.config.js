const fs = require('fs');
const evalSourceMapMiddleware = require('react-dev-utils/evalSourceMapMiddleware');
const noopServiceWorkerMiddleware = require('react-dev-utils/noopServiceWorkerMiddleware');
const redirectServedPath = require('react-dev-utils/redirectServedPathMiddleware');
const paths = require('react-scripts/config/paths');

module.exports = {
  devServer: (devServerConfig, { env, paths }) => {
    // Completely override the devServer config to be compatible with webpack-dev-server 5.x
    const host = process.env.HOST || '0.0.0.0';
    const sockHost = process.env.WDS_SOCKET_HOST;
    const sockPath = process.env.WDS_SOCKET_PATH;
    const sockPort = process.env.WDS_SOCKET_PORT;
    
    return {
      allowedHosts: 'all',
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': '*',
        'Access-Control-Allow-Headers': '*',
      },
      compress: true,
      static: {
        directory: paths.appPublic,
        publicPath: [paths.publicUrlOrPath],
        watch: {
          ignored: /node_modules/,
        },
      },
      client: {
        webSocketURL: {
          hostname: sockHost,
          pathname: sockPath,
          port: sockPort,
        },
        overlay: {
          errors: true,
          warnings: false,
        },
      },
      devMiddleware: {
        publicPath: paths.publicUrlOrPath.slice(0, -1),
      },
      host,
      historyApiFallback: {
        disableDotRule: true,
        index: paths.publicUrlOrPath,
      },
      
      // Replace deprecated middleware setup with setupMiddlewares
      setupMiddlewares: (middlewares, devServer) => {
        if (!devServer) {
          throw new Error('webpack-dev-server is not defined');
        }
        
        // Add evalSourceMapMiddleware (was in onBeforeSetupMiddleware)
        devServer.app.use(evalSourceMapMiddleware(devServer));
        
        // Add proxy setup if exists
        if (fs.existsSync(paths.proxySetup)) {
          require(paths.proxySetup)(devServer.app);
        }
        
        // Add redirectServedPath middleware (was in onAfterSetupMiddleware)
        devServer.app.use(redirectServedPath(paths.publicUrlOrPath));
        
        // Add noopServiceWorkerMiddleware (was in onAfterSetupMiddleware)
        devServer.app.use(noopServiceWorkerMiddleware(paths.publicUrlOrPath));
        
        return middlewares;
      },
    };
  },
};