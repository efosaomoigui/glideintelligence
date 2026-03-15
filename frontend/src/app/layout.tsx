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
  metadataBase: new URL("https://paperly.intelligence.glide"), // Placeholder for absolute URLs
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "PAPERLY. | AI News Intelligence",
    description: "Synthesized intelligence and contextual analysis of West African news.",
    url: "https://paperly.intelligence.glide",
    siteName: "PAPERLY.",
    images: [
      {
        url: "/icon.png",
        width: 1200,
        height: 630,
        alt: "PAPERLY. Intelligence",
      },
    ],
    locale: "en_NG",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PAPERLY. | AI News Intelligence",
    description: "We don't publish news. We make sense of it.",
    images: ["/icon.png"],
  },
  icons: {
    icon: "/icon.png",
    apple: "/apple-icon.png",
  },
};

import { AuthProvider } from "@/context/AuthContext";

const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://paperly.intelligence.glide/#organization",
      "name": "PAPERLY.",
      "url": "https://paperly.intelligence.glide",
      "logo": {
        "@type": "ImageObject",
        "url": "https://paperly.intelligence.glide/icon.png"
      },
      "description": "AI-Powered News Intelligence Platform for Nigeria & West Africa. We synthesize news from hundreds of sources into clear, structured intelligence reports.",
      "areaServed": ["Nigeria", "West Africa", "ECOWAS"],
      "knowsAbout": ["Nigerian Politics", "West African Economy", "Security Intelligence", "Business Analysis", "Technology in Africa"],
      "sameAs": []
    },
    {
      "@type": "WebSite",
      "@id": "https://paperly.intelligence.glide/#website",
      "url": "https://paperly.intelligence.glide",
      "name": "PAPERLY.",
      "description": "AI-Powered News Intelligence for Nigeria & West Africa",
      "publisher": {
        "@id": "https://paperly.intelligence.glide/#organization"
      },
      "potentialAction": {
        "@type": "SearchAction",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "https://paperly.intelligence.glide/?q={search_term_string}"
        },
        "query-input": "required name=search_term_string"
      },
      "inLanguage": "en-NG"
    }
  ]
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en-NG">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body suppressHydrationWarning className={`${inter.variable} ${sora.variable} ${playfair.variable} ${jetbrainsMono.variable}`}>
        <AuthProvider>
          {children}
          <DetailFlyout />
        </AuthProvider>
      </body>
    </html>
  );
}
