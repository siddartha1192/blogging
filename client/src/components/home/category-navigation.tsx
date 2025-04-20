import React from "react";
import { Link } from "wouter";
import { useCategories } from "@/hooks/use-categories";
import { ChartLine, Bot, Newspaper } from "lucide-react";

const CategoryNavigation: React.FC = () => {
  const { data: categories, isLoading } = useCategories();

  if (isLoading || !categories) {
    return (
      <section className="mb-12">
        <div className="flex flex-wrap md:flex-nowrap gap-4 justify-center">
          {[1, 2, 3].map((i) => (
            <div key={i} className="w-full md:w-1/3 bg-gray-100 rounded-xl h-48 animate-pulse" />
          ))}
        </div>
      </section>
    );
  }

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

  return (
    <section className="mb-12">
      <div className="flex flex-wrap md:flex-nowrap gap-4 justify-center">
        {categories.map((category) => (
          <Link 
            key={category.id}
            href={`/category/${category.slug}`} 
            className="w-full md:w-1/3 bg-white hover:bg-gray-50 rounded-xl shadow-md transition-transform hover:scale-105 overflow-hidden"
          >
            <div 
              className={`h-24 category-${category.slug} flex items-center justify-center`}
              style={{ backgroundColor: category.color }}
            >
              {getCategoryIcon(category.slug)}
            </div>
            <div className="p-5 text-center">
              <h3 className="text-lg font-semibold mb-2">{category.name}</h3>
              <p className="text-gray-600 text-sm">{category.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
};

export default CategoryNavigation;
