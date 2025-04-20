import React from "react";
import { Link } from "wouter";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { Post } from "@shared/schema";

interface PostCardProps {
  post: Post & {
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
  };
}

const PostCard: React.FC<PostCardProps> = ({ post }) => {
  // Determine badge variant based on category
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

  return (
    <article className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
      <Link href={`/post/${post.slug}`}>
        <div>
          <img 
            src={post.featuredImage} 
            alt={post.title} 
            className="w-full h-48 object-cover"
          />
          <div className="p-5">
            <Badge 
              variant={getBadgeVariant(post.category.slug)} 
              className="mb-2 uppercase"
            >
              {post.category.name}
            </Badge>
            <h3 className="text-lg font-semibold mb-2">{post.title}</h3>
            <p className="text-gray-600 text-sm mb-4 line-clamp-3">{post.excerpt}</p>
            <div className="flex justify-between items-center">
              <div className="flex items-center">
                <img 
                  src={post.author.avatar} 
                  alt={post.author.name} 
                  className="w-6 h-6 rounded-full mr-2"
                />
                <span className="text-xs text-gray-500">{post.author.name}</span>
              </div>
              <span className="text-xs text-gray-500">{formatDate(post.publishDate)}</span>
            </div>
          </div>
        </div>
      </Link>
    </article>
  );
};

export default PostCard;
