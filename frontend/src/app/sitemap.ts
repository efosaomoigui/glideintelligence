import { MetadataRoute } from "next";

const BASE_URL = "https://paperly.online";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const categories = [
  "economy",
  "politics",
  "business",
  "security",
  "technology",
  "regional",
  "global-impact",
  "sport",
];

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const routes = [
    {
      url: BASE_URL,
      lastModified: new Date(),
      changeFrequency: "always" as const,
      priority: 1,
    },
    ...categories.map((cat) => ({
      url: `${BASE_URL}/${cat}`,
      lastModified: new Date(),
      changeFrequency: "hourly" as const,
      priority: 0.8,
    })),
  ];

  try {
    const res = await fetch(`${API_URL}/api/topics/trending?limit=100`, {
      next: { revalidate: 3600 },
    });

    if (res.ok) {
      const data = await res.json();
      const topics = data.items || [];

      const topicRoutes = topics.map((topic: any) => ({
        url: `${BASE_URL}/topic/${topic.slug || topic.id}`,
        lastModified: new Date(topic.updated_at || new Date()),
        changeFrequency: "daily" as const,
        priority: 0.6,
      }));

      return [...routes, ...topicRoutes];
    }
  } catch (error) {
    console.error("Error generating sitemap:", error);
  }

  return routes;
}
