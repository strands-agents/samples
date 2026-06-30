// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AG-UI Strands Sample",
  description: "Strands SDK + AG-UI/CopilotKit Integration Sample",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
