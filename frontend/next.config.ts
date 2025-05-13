import type { NextConfig } from "next";
import MiniCssExtractPlugin from "mini-css-extract-plugin";
import type { Configuration as WebpackConfiguration } from "webpack";

const nextConfig: NextConfig = {
  /* config options here */

  webpack: (config: WebpackConfiguration) => {
    if (config.resolve) {
      config.resolve.alias = {
        ...config.resolve.alias,
        canvas: false,
      };
    }

    if (config.plugins) {
      config.plugins.push(new MiniCssExtractPlugin());
    }

    return config;
  },
};

export default nextConfig;
