import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { Topic } from "@shared/schema";

const TrendingTopics: React.FC = () => {
  const { data: topics, isLoading, error } = useQuery<Topic[]>({
    queryKey: ["/api/topics"],
  });

  if (isLoading) {
    return (
      <section className="mb-16">
        <h2 className="text-2xl font-bold mb-8">Trending Topics</h2>
        <div className="flex flex-wrap gap-3">
          {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
            <div 
              key={i} 
              className="h-8 bg-gray-200 rounded-full animate-pulse" 
              style={{ width: `${Math.floor(Math.random() * 100) + 100}px` }}
            ></div>
          ))}
        </div>
      </section>
    );
  }

  if (error || !topics || topics.length === 0) {
    return (
      <section className="mb-16">
        <h2 className="text-2xl font-bold mb-8">Trending Topics</h2>
        <p className="text-gray-600">No trending topics available at the moment.</p>
      </section>
    );
  }

  return (
    <section className="mb-16">
      <h2 className="text-2xl font-bold mb-8">Trending Topics</h2>
      <div className="flex flex-wrap gap-3">
        {topics.map((topic) => (
          <Link 
            key={topic.id} 
            href={`/topic/${topic.slug}`} 
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 text-sm transition-colors"
          >
            #{topic.name}
          </Link>
        ))}
      </div>
    </section>
  );
};

export default TrendingTopics;
