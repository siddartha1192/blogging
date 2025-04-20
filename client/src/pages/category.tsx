import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useRoute } from "wouter";
import Header from "@/components/layout/header";
import Footer from "@/components/layout/footer";
import PostCard from "@/components/post/post-card";
import Newsletter from "@/components/home/newsletter";
import { useCategory } from "@/hooks/use-categories";
import { ChartLine, Bot, Newspaper } from "lucide-react";
import { Post, Category } from "@shared/schema";

interface EnhancedPost extends Post {
  author: {
    id: number;
    name: string;
    avatar: string;
  };
  category: {
    id: number;
    name: string;
    slug: string;
    color: string;
  };
}

const CategoryPage: React.FC = () => {
  const [match, params] = useRoute<{ slug: string }>("/category/:slug");
  const slug = params?.slug || "";
  
  const { data: category } = useCategory(slug);
  
  const { data: posts, isLoading, error } = useQuery<EnhancedPost[]>({
    queryKey: [`/api/posts/category/${slug}`],
    enabled: !!slug,
  });

  // Get icon based on category slug
  const getCategoryIcon = (slug: string) => {
    switch (slug) {
      case "finance":
        return <ChartLine className="text-white text-4xl" />;
      case "automation":
        return <Bot className="text-white text-4xl" />;
      case "tech-news":
        return <Newspaper className="text-white text-4xl" />;
      default:
        return <Newspaper className="text-white text-4xl" />;
    }
  };

  if (!match) {
    return null;
  }

  return (
    <>
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Category Header */}
        {category && (
          <div className="mb-12">
            <div 
              className={`py-16 px-8 rounded-xl mb-6 flex items-center justify-center category-${category.slug}`}
              style={{ backgroundColor: category.color }}
            >
              <div className="text-center text-white">
                {getCategoryIcon(category.slug)}
                <h1 className="text-3xl md:text-4xl font-bold mt-4">{category.name}</h1>
                <p className="mt-2 max-w-2xl mx-auto">{category.description}</p>
              </div>
            </div>
          </div>
        )}

        {/* Posts Grid */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold mb-8">
            {category ? `All ${category.name} Articles` : "Loading..."}
          </h2>
          
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="bg-white rounded-lg shadow-md overflow-hidden">
                  <div className="w-full h-48 bg-gray-200 animate-pulse"></div>
                  <div className="p-5">
                    <div className="w-24 h-6 bg-gray-200 rounded animate-pulse mb-2"></div>
                    <div className="w-full h-6 bg-gray-200 rounded animate-pulse mb-2"></div>
                    <div className="w-full h-4 bg-gray-200 rounded animate-pulse mb-2"></div>
                    <div className="w-2/3 h-4 bg-gray-200 rounded animate-pulse mb-4"></div>
                    <div className="flex justify-between">
                      <div className="flex items-center">
                        <div className="w-6 h-6 bg-gray-200 rounded-full animate-pulse mr-2"></div>
                        <div className="w-20 h-4 bg-gray-200 rounded animate-pulse"></div>
                      </div>
                      <div className="w-16 h-4 bg-gray-200 rounded animate-pulse"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : error || !posts ? (
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold mb-2">Error Loading Articles</h3>
              <p className="text-gray-600">Unable to load articles for this category. Please try again later.</p>
            </div>
          ) : posts.length === 0 ? (
            <div className="bg-white p-6 rounded-lg shadow-md text-center">
              <h3 className="text-lg font-semibold mb-2">No Articles Found</h3>
              <p className="text-gray-600">There are no articles in this category yet. Check back later!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {posts.map((post) => (
                <PostCard key={post.id} post={post} />
              ))}
            </div>
          )}
        </section>

        <Newsletter />
      </main>
      <Footer />
    </>
  );
};

export default CategoryPage;
