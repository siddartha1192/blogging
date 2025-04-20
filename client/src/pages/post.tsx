import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useRoute, Link } from "wouter";
import Header from "@/components/layout/header";
import Footer from "@/components/layout/footer";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { formatDate } from "@/lib/utils";
import Newsletter from "@/components/home/newsletter";
import TrendingTopics from "@/components/home/trending-topics";
import { Post } from "@shared/schema";

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

const PostPage: React.FC = () => {
  const [match, params] = useRoute<{ slug: string }>("/post/:slug");
  const slug = params?.slug || "";
  
  const { data: post, isLoading, error } = useQuery<EnhancedPost>({
    queryKey: [`/api/posts/${slug}`],
    enabled: !!slug,
  });

  // Determine badge variant based on category
  const getBadgeVariant = (categorySlug?: string) => {
    if (!categorySlug) return "default";
    
    switch (categorySlug) {
      case "finance":
        return "finance";
      case "automation":
        return "automation";
      case "tech-news":
        return "technews";
      default:
        return "default";
    }
  };

  if (!match) {
    return null;
  }

  return (
    <>
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="bg-white rounded-xl shadow-md p-8 animate-pulse">
            <div className="w-32 h-6 bg-gray-200 rounded mb-4"></div>
            <div className="w-full h-12 bg-gray-200 rounded mb-6"></div>
            <div className="flex items-center mb-8">
              <div className="w-12 h-12 bg-gray-200 rounded-full mr-4"></div>
              <div>
                <div className="w-32 h-4 bg-gray-200 rounded mb-2"></div>
                <div className="w-48 h-3 bg-gray-200 rounded"></div>
              </div>
            </div>
            <div className="w-full h-64 bg-gray-200 rounded mb-8"></div>
            <div className="space-y-4">
              <div className="w-full h-5 bg-gray-200 rounded"></div>
              <div className="w-full h-5 bg-gray-200 rounded"></div>
              <div className="w-full h-5 bg-gray-200 rounded"></div>
              <div className="w-full h-5 bg-gray-200 rounded"></div>
              <div className="w-2/3 h-5 bg-gray-200 rounded"></div>
            </div>
          </div>
        ) : error || !post ? (
          <div className="bg-white rounded-xl shadow-md p-8">
            <h1 className="text-2xl font-bold text-gray-800 mb-4">Post Not Found</h1>
            <p className="text-gray-600 mb-8">The post you're looking for couldn't be found or may have been removed.</p>
            <Link href="/" className="text-primary hover:underline">Return to Home</Link>
          </div>
        ) : (
          <>
            <article className="bg-white rounded-xl shadow-md overflow-hidden mb-12">
              <div className="p-8">
                <Link href={`/category/${post.category.slug}`}>
                  <Badge 
                    variant={getBadgeVariant(post.category.slug)} 
                    className="mb-4 uppercase"
                  >
                    {post.category.name}
                  </Badge>
                </Link>
                <h1 className="text-3xl md:text-4xl font-bold mb-6">{post.title}</h1>
                <div className="flex items-center mb-8">
                  <img 
                    src={post.author.avatar} 
                    alt={post.author.name} 
                    className="w-12 h-12 rounded-full mr-4"
                  />
                  <div>
                    <p className="font-medium">{post.author.name}</p>
                    <p className="text-sm text-gray-500">
                      {formatDate(post.publishDate)} · {post.readTime} min read
                    </p>
                  </div>
                </div>
                <img 
                  src={post.featuredImage} 
                  alt={post.title} 
                  className="w-full h-auto rounded-lg mb-8"
                />
                <div className="prose prose-lg max-w-none">
                  {post.content.split('\n').map((paragraph, index) => (
                    <p key={index} className="mb-4">{paragraph}</p>
                  ))}
                </div>
              </div>
            </article>
            
            <Separator className="my-12" />
            
            <TrendingTopics />
            <Newsletter />
          </>
        )}
      </main>
      <Footer />
    </>
  );
};

export default PostPage;
