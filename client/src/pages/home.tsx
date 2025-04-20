import React from "react";
import Header from "@/components/layout/header";
import Footer from "@/components/layout/footer";
import FeaturedSlider from "@/components/home/featured-slider";
import CategoryNavigation from "@/components/home/category-navigation";
import LatestArticles from "@/components/home/latest-articles";
import Newsletter from "@/components/home/newsletter";
import TrendingTopics from "@/components/home/trending-topics";

const Home: React.FC = () => {
  return (
    <>
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <FeaturedSlider />
        <CategoryNavigation />
        <LatestArticles />
        <Newsletter />
        <TrendingTopics />
      </main>
      <Footer />
    </>
  );
};

export default Home;
