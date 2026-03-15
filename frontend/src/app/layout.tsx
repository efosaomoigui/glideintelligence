import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Sora, Playfair_Display, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import "./mobile.css";
import DetailFlyout from "@/components/DetailFlyout";


const inter = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const sora = Sora({
  subsets: ["latin"],
  variable: "--font-sora",
  display: "swap",
  weight: ["600", "700"],
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
  display: "swap",
  weight: ["400", "600", "800"],
  style: ["normal", "italic"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "PAPERLY. | Making Sense of the News",
  description:
    "AI-Powered Intelligence Platform for Nigeria & West Africa - We don't publish news. We make sense of it.",
};

import { AuthProvider } from "@/context/AuthContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body suppressHydrationWarning className={`${inter.variable} ${sora.variable} ${playfair.variable} ${jetbrainsMono.variable}`}>
        <AuthProvider>
          {children}
          <DetailFlyout />
        </AuthProvider>
      </body>
    </html>
  );
}
