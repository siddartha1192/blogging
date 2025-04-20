import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Carousel, 
  CarouselContent, 
  CarouselItem, 
  CarouselPrevious, 
  CarouselNext,
  CarouselProgressDots 
} from "@/components/ui/carousel";
import { ChevronRight } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { SLIDER_DURATION } from "@/lib/constants";
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

const FeaturedSlider: React.FC = () => {
  const { data: featuredPosts, isLoading, error } = useQuery<EnhancedPost[]>({
    queryKey: ["/api/posts/featured"],
  });

  // Function to determine badge variant based on category
  const getBadgeVariant = (categorySlug: string) => {
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

  if (isLoading) {
    return (
      <section className="mb-16">
        <div className="relative bg-white rounded-xl shadow-md overflow-hidden h-[400px] md:h-[500px] animate-pulse">
          <div className="flex items-center justify-center h-full">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        </div>
      </section>
    );
  }

  if (error || !featuredPosts || featuredPosts.length === 0) {
    return (
      <section className="mb-16">
        <div className="relative bg-white rounded-xl shadow-md overflow-hidden">
          <div className="p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">No Featured Posts</h2>
            <p className="text-gray-600">Check back later for featured content.</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="mb-16">
      <div className="relative bg-white rounded-xl shadow-md overflow-hidden">
        <Carousel interval={SLIDER_DURATION} opts={{ loop: true }}>
          <CarouselContent>
            {featuredPosts.map((post) => (
              <CarouselItem key={post.id}>
                <div className="grid grid-cols-1 md:grid-cols-2 h-[400px] md:h-[500px]">
                  <div className="p-8 md:p-12 flex flex-col justify-center">
                    <div className="inline-block">
                      <Badge 
                        variant={getBadgeVariant(post.category.slug)} 
                        className="mb-4 uppercase"
                      >
                        {post.category.name}
                      </Badge>
                    </div>
                    <h2 className="text-2xl md:text-4xl font-bold mb-4">{post.title}</h2>
                    <p className="text-gray-600 mb-6 line-clamp-3 md:line-clamp-4">{post.excerpt}</p>
                    <div className="flex items-center mb-6">
                      <img 
                        src={post.author.avatar} 
                        alt={`${post.author.name} avatar`} 
                        className="w-10 h-10 rounded-full mr-3"
                      />
                      <div>
                        <p className="text-sm font-medium">{post.author.name}</p>
                        <p className="text-xs text-gray-500">
                          {formatDate(post.publishDate)} · {post.readTime} min read
                        </p>
                      </div>
                    </div>
                    <Link href={`/post/${post.slug}`}>
                      <Button className="inline-flex items-center">
                        Read Article
                        <ChevronRight className="ml-2 h-4 w-4" />
                      </Button>
                    </Link>
                  </div>
                  <div className="hidden md:block">
                    <img
                      src={post.featuredImage}
                      alt={post.title}
                      className="h-full w-full object-cover"
                    />
                  </div>
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>
          
          <div className="absolute bottom-4 left-0 right-0 flex justify-center">
            <CarouselProgressDots />
          </div>
          
          <CarouselPrevious className="bg-white/80 hover:bg-white text-gray-800" />
          <CarouselNext className="bg-white/80 hover:bg-white text-gray-800" />
        </Carousel>
      </div>
    </section>
  );
};

export default FeaturedSlider;
