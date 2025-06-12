import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import { UploadProvider } from "@/contexts/UploadContext";
import { UploadProgressContainer } from "@/components/UploadProgressContainer";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DocManager",
  description: "Document Management Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <UploadProvider>
          {children}
          <UploadProgressContainer />
          <Toaster position="top-right" />
        </UploadProvider>
      </body>
    </html>
  );
}
