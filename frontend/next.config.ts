import type { NextConfig } from "next";
import MiniCssExtractPlugin from "mini-css-extract-plugin";
import type { Configuration as WebpackConfiguration } from "webpack";

const nextConfig: NextConfig = {
  /* config options here */

  webpack: (config: WebpackConfiguration, { isServer }) => {
    config.plugins = config.plugins || [];

    if (!isServer) {
      config.plugins.push(new MiniCssExtractPlugin());
    }

    return config;
  },
};

export default nextConfig;
