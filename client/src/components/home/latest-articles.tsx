import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";
import PostCard from "@/components/post/post-card";
import { useCategories } from "@/hooks/use-categories";
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

const LatestArticles: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [visiblePosts, setVisiblePosts] = useState<number>(6);
  
  const { data: categories } = useCategories();

  const { data: posts, isLoading, error } = useQuery<EnhancedPost[]>({
    queryKey: ["/api/posts", selectedCategory !== "all" ? { category: selectedCategory } : null],
  });

  const handleCategoryChange = (value: string) => {
    setSelectedCategory(value);
    setVisiblePosts(6); // Reset visible posts when changing category
  };

  const loadMorePosts = () => {
    setVisiblePosts((prev) => prev + 3);
  };

  // Display skeleton loading
  if (isLoading) {
    return (
      <section className="mb-16">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold">Latest Articles</h2>
          <div className="w-40 h-10 bg-gray-200 rounded animate-pulse"></div>
        </div>
        
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
      </section>
    );
  }

  // Display error message
  if (error || !posts) {
    return (
      <section className="mb-16">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Error Loading Articles</h2>
          <p className="text-gray-600">Unable to load the latest articles. Please try again later.</p>
        </div>
      </section>
    );
  }

  // Filter posts by category if selected
  const filteredPosts = selectedCategory !== "all" 
    ? posts.filter(post => post.category.slug === selectedCategory)
    : posts;

  const displayedPosts = filteredPosts.slice(0, visiblePosts);
  const hasMorePosts = displayedPosts.length < filteredPosts.length;

  return (
    <section className="mb-16">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold">Latest Articles</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Filter by:</span>
          <Select value={selectedCategory} onValueChange={handleCategoryChange}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All Categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Categories</SelectItem>
              {categories?.map((category) => (
                <SelectItem key={category.id} value={category.slug}>
                  {category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      
      {displayedPosts.length === 0 ? (
        <div className="bg-white p-6 rounded-lg shadow-md text-center">
          <h3 className="text-lg font-semibold mb-2">No Articles Found</h3>
          <p className="text-gray-600 mb-4">There are no articles in this category yet.</p>
          <Button variant="outline" onClick={() => setSelectedCategory("all")}>
            View All Categories
          </Button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayedPosts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
          
          {hasMorePosts && (
            <div className="mt-8 flex justify-center">
              <Button
                variant="outline"
                onClick={loadMorePosts}
                className="inline-flex items-center"
              >
                Load More Articles
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}
    </section>
  );
};

export default LatestArticles;
