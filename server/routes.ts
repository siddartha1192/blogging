import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { z } from "zod";
import { insertPostSchema } from "@shared/schema";

export async function registerRoutes(app: Express): Promise<Server> {
  // prefix all routes with /api
  
  // Categories API
  app.get("/api/categories", async (req, res) => {
    try {
      const categories = await storage.getAllCategories();
      res.json(categories);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch categories" });
    }
  });
  
  app.get("/api/categories/:slug", async (req, res) => {
    try {
      const category = await storage.getCategoryBySlug(req.params.slug);
      if (!category) {
        return res.status(404).json({ message: "Category not found" });
      }
      res.json(category);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch category" });
    }
  });
  
  // Posts API
  app.get("/api/posts", async (req, res) => {
    try {
      const categorySlug = req.query.category as string | undefined;
      
      let posts;
      if (categorySlug) {
        posts = await storage.getPostsByCategorySlug(categorySlug);
      } else {
        posts = await storage.getAllPosts();
      }
      
      // Get all authors to populate post data
      const authors = await storage.getAllAuthors();
      const categories = await storage.getAllCategories();
      
      // Enhance posts with author and category data
      const enhancedPosts = await Promise.all(
        posts.map(async (post) => {
          const author = authors.find(a => a.id === post.authorId);
          const category = categories.find(c => c.id === post.categoryId);
          
          return {
            ...post,
            author,
            category
          };
        })
      );
      
      res.json(enhancedPosts);
    } catch (error) {
      console.error("Error fetching posts:", error);
      res.status(500).json({ message: "Failed to fetch posts" });
    }
  });
  
  app.get("/api/posts/featured", async (req, res) => {
    try {
      const featuredPosts = await storage.getFeaturedPosts();
      
      // Get all authors to populate post data
      const authors = await storage.getAllAuthors();
      const categories = await storage.getAllCategories();
      
      // Enhance posts with author and category data
      const enhancedPosts = await Promise.all(
        featuredPosts.map(async (post) => {
          const author = authors.find(a => a.id === post.authorId);
          const category = categories.find(c => c.id === post.categoryId);
          
          return {
            ...post,
            author,
            category
          };
        })
      );
      
      res.json(enhancedPosts);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch featured posts" });
    }
  });
  
  app.get("/api/posts/category/:slug", async (req, res) => {
    try {
      const posts = await storage.getPostsByCategorySlug(req.params.slug);
      
      // Get all authors to populate post data
      const authors = await storage.getAllAuthors();
      const categories = await storage.getAllCategories();
      
      // Enhance posts with author and category data
      const enhancedPosts = await Promise.all(
        posts.map(async (post) => {
          const author = authors.find(a => a.id === post.authorId);
          const category = categories.find(c => c.id === post.categoryId);
          
          return {
            ...post,
            author,
            category
          };
        })
      );
      
      res.json(enhancedPosts);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch posts by category" });
    }
  });
  
  app.get("/api/posts/:slug", async (req, res) => {
    try {
      const post = await storage.getPostBySlug(req.params.slug);
      if (!post) {
        return res.status(404).json({ message: "Post not found" });
      }
      
      // Get author and category data
      const author = await storage.getAuthor(post.authorId);
      const category = await storage.getCategoryBySlug(
        (await storage.getAllCategories()).find(c => c.id === post.categoryId)?.slug || ""
      );
      
      res.json({
        ...post,
        author,
        category
      });
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch post" });
    }
  });
  
  app.post("/api/posts", async (req, res) => {
    try {
      const validatedData = insertPostSchema.parse(req.body);
      const post = await storage.createPost(validatedData);
      res.status(201).json(post);
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ message: "Invalid post data", errors: error.errors });
      }
      res.status(500).json({ message: "Failed to create post" });
    }
  });
  
  // Authors API
  app.get("/api/authors", async (req, res) => {
    try {
      const authors = await storage.getAllAuthors();
      res.json(authors);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch authors" });
    }
  });
  
  // Topics API
  app.get("/api/topics", async (req, res) => {
    try {
      const topics = await storage.getAllTopics();
      res.json(topics);
    } catch (error) {
      res.status(500).json({ message: "Failed to fetch topics" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
