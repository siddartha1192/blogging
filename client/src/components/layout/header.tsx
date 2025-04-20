import React, { useState } from "react";
import { Link, useLocation } from "wouter";
import { useCategories } from "@/hooks/use-categories";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Microchip, Search, Menu, X } from "lucide-react";
import { BLOG_TITLE } from "@/lib/constants";

const Header: React.FC = () => {
  const [location] = useLocation();
  const { data: categories } = useCategories();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Implement search functionality
    console.log("Searching for:", searchQuery);
  };

  const isActive = (path: string) => {
    return location === path;
  };

  return (
    <header className="bg-white shadow-sm sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center">
            <Link href="/" className="text-primary font-bold text-xl flex items-center gap-2">
              <Microchip className="h-6 w-6" />
              <span>{BLOG_TITLE}</span>
            </Link>
          </div>
          
          {/* Navigation - Desktop */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link 
              href="/" 
              className={`nav-link font-medium ${isActive('/') ? 'text-gray-900 active' : 'text-gray-500'} hover:text-primary transition-colors`}
            >
              Home
            </Link>
            {categories?.map((category) => (
              <Link
                key={category.id}
                href={`/category/${category.slug}`}
                className={`nav-link font-medium ${isActive(`/category/${category.slug}`) ? 'text-gray-900 active' : 'text-gray-500'} hover:text-primary transition-colors`}
              >
                {category.name}
              </Link>
            ))}
          </nav>
          
          {/* Search */}
          <div className="hidden md:flex items-center">
            <form onSubmit={handleSearch} className="relative">
              <Input 
                type="text" 
                placeholder="Search posts..." 
                className="w-64 py-2 pl-10 pr-4 rounded-md"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
            </form>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={toggleMobileMenu} 
              className="text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none"
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </Button>
          </div>
        </div>
      </div>
      
      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link
              href="/"
              className={`block px-3 py-2 rounded-md text-base font-medium ${
                isActive('/') ? 'text-primary bg-gray-50' : 'text-gray-700 hover:text-primary hover:bg-gray-50'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              Home
            </Link>
            {categories?.map((category) => (
              <Link
                key={category.id}
                href={`/category/${category.slug}`}
                className={`block px-3 py-2 rounded-md text-base font-medium ${
                  isActive(`/category/${category.slug}`) ? 'text-primary bg-gray-50' : 'text-gray-700 hover:text-primary hover:bg-gray-50'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {category.name}
              </Link>
            ))}
          </div>
          <div className="px-5 py-3 border-t border-gray-200">
            <form onSubmit={handleSearch} className="relative">
              <Input 
                type="text" 
                placeholder="Search posts..." 
                className="w-full py-2 pl-10 pr-4 rounded-md"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
