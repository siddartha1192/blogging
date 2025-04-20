import {
  users, User, InsertUser,
  categories, Category, InsertCategory,
  posts, Post, InsertPost,
  authors, Author, InsertAuthor,
  topics, Topic, InsertTopic
} from "@shared/schema";

export interface IStorage {
  // User methods
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Category methods
  getAllCategories(): Promise<Category[]>;
  getCategoryBySlug(slug: string): Promise<Category | undefined>;
  createCategory(category: InsertCategory): Promise<Category>;
  
  // Post methods
  getAllPosts(): Promise<Post[]>;
  getFeaturedPosts(): Promise<Post[]>;
  getPostsByCategory(categoryId: number): Promise<Post[]>;
  getPostsByCategorySlug(slug: string): Promise<Post[]>;
  getPostBySlug(slug: string): Promise<Post | undefined>;
  createPost(post: InsertPost): Promise<Post>;
  
  // Author methods
  getAllAuthors(): Promise<Author[]>;
  getAuthor(id: number): Promise<Author | undefined>;
  createAuthor(author: InsertAuthor): Promise<Author>;
  
  // Topic methods
  getAllTopics(): Promise<Topic[]>;
  createTopic(topic: InsertTopic): Promise<Topic>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private categories: Map<number, Category>;
  private posts: Map<number, Post>;
  private authors: Map<number, Author>;
  private topics: Map<number, Topic>;
  
  private userId: number;
  private categoryId: number;
  private postId: number;
  private authorId: number;
  private topicId: number;

  constructor() {
    this.users = new Map();
    this.categories = new Map();
    this.posts = new Map();
    this.authors = new Map();
    this.topics = new Map();
    
    this.userId = 1;
    this.categoryId = 1;
    this.postId = 1;
    this.authorId = 1;
    this.topicId = 1;
    
    this.initializeData();
  }
  
  private initializeData() {
    // Initialize default categories
    const financeCategory: InsertCategory = {
      name: "Finance",
      slug: "finance",
      description: "Explore the latest in financial technology and market trends",
      iconName: "chart-line",
      color: "#F59E0B",
    };
    
    const automationCategory: InsertCategory = {
      name: "Automation",
      slug: "automation",
      description: "Discover AI, machine learning, and automation innovations",
      iconName: "robot",
      color: "#10B981",
    };
    
    const techNewsCategory: InsertCategory = {
      name: "Tech News",
      slug: "tech-news",
      description: "Stay updated with breaking technology news and releases",
      iconName: "newspaper",
      color: "#EF4444",
    };
    
    this.createCategory(financeCategory);
    this.createCategory(automationCategory);
    this.createCategory(techNewsCategory);
    
    // Initialize default authors
    const authors = [
      { name: "Alex Johnson", avatar: "https://images.unsplash.com/photo-1633332755192-727a05c4013d?q=80&w=40&h=40&auto=format&fit=crop" },
      { name: "Sarah Chen", avatar: "https://images.unsplash.com/photo-1580489944761-15a19d654956?q=80&w=40&h=40&auto=format&fit=crop" },
      { name: "Michael Torres", avatar: "https://images.unsplash.com/photo-1607990281513-2c110a25bd8c?q=80&w=40&h=40&auto=format&fit=crop" },
      { name: "David Kim", avatar: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?q=80&w=30&h=30&auto=format&fit=crop" },
      { name: "Emily Wong", avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=30&h=30&auto=format&fit=crop" },
      { name: "Ryan Brooks", avatar: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=30&h=30&auto=format&fit=crop" },
    ];
    
    authors.forEach(author => this.createAuthor(author));
    
    // Initialize default posts
    const defaultPosts: Omit<InsertPost, "authorId" | "categoryId">[] = [
      {
        title: "The Future of Cryptocurrency in Banking",
        slug: "future-cryptocurrency-banking",
        excerpt: "Explore how blockchain technologies are transforming traditional banking systems and what it means for the future of finance and digital transactions.",
        content: "Cryptocurrency is revolutionizing the banking industry in ways we couldn't have imagined a decade ago. Banks are now actively exploring blockchain technologies to improve transaction speeds, reduce costs, and enhance security. This article explores the implications of this transformation and what it means for consumers and financial institutions alike.",
        featuredImage: "https://images.unsplash.com/photo-1621761191319-c6fb62004040?q=80&w=600&h=500&auto=format&fit=crop",
        featured: true,
        readTime: 8,
      },
      {
        title: "AI-Powered Home Automation: The Smart Home Revolution",
        slug: "ai-powered-home-automation",
        excerpt: "Discover how artificial intelligence is revolutionizing home automation systems, making our living spaces more efficient, secure, and personalized.",
        content: "Smart homes are getting smarter thanks to AI. From predictive temperature adjustments to security systems that can distinguish between family members and intruders, artificial intelligence is transforming our living spaces in remarkable ways. This article examines the latest innovations and what they mean for the future of home living.",
        featuredImage: "https://images.unsplash.com/photo-1585503418537-88331351ad99?q=80&w=600&h=500&auto=format&fit=crop",
        featured: true,
        readTime: 6,
      },
      {
        title: "Apple's New M3 Chip: A Quantum Leap in Computing",
        slug: "apple-m3-chip-quantum-leap",
        excerpt: "An in-depth look at Apple's groundbreaking M3 processor and how it's changing the landscape of personal computing with unprecedented performance and efficiency.",
        content: "Apple's M3 chip represents a significant advancement in computing architecture. With improvements in energy efficiency, processing power, and integrated AI capabilities, the M3 is redefining what's possible in consumer electronics. This article breaks down the technical specifications and real-world implications of this revolutionary processor.",
        featuredImage: "https://images.unsplash.com/photo-1543285198-3af15c4592ce?q=80&w=600&h=500&auto=format&fit=crop",
        featured: true,
        readTime: 10,
      },
      {
        title: "Digital Wallets: The End of Physical Banking?",
        slug: "digital-wallets-end-physical-banking",
        excerpt: "As digital wallets gain popularity, traditional banking institutions are facing new challenges in customer retention and service delivery.",
        content: "Digital wallets are becoming the preferred method of payment for millions of consumers worldwide. This shift is forcing traditional banks to rethink their business models and service offerings. This article explores the rise of digital payment solutions and what it means for the future of physical banking locations and services.",
        featuredImage: "https://images.unsplash.com/photo-1526378722484-bd91ca387e72?q=80&w=400&h=225&auto=format&fit=crop",
        featured: false,
        readTime: 7,
      },
      {
        title: "Machine Learning in Healthcare: Saving Lives with AI",
        slug: "machine-learning-healthcare-saving-lives",
        excerpt: "How machine learning algorithms are revolutionizing disease diagnosis and treatment planning in modern healthcare systems.",
        content: "Healthcare is being transformed by machine learning technologies that can detect patterns and anomalies that might escape even the most experienced human physicians. From early cancer detection to personalized treatment plans, AI is helping save lives and improve patient outcomes. This article examines the most promising applications and ethical considerations.",
        featuredImage: "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?q=80&w=400&h=225&auto=format&fit=crop",
        featured: false,
        readTime: 9,
      },
      {
        title: "Samsung Unveils Revolutionary Folding Phone Technology",
        slug: "samsung-folding-phone-technology",
        excerpt: "Samsung's latest innovation pushes the boundaries of smartphone design with a triple-folding display and enhanced durability.",
        content: "Samsung continues to lead the folding phone market with its latest breakthrough in display technology. The new triple-folding design offers unprecedented versatility while addressing durability concerns that have plagued earlier models. This article provides an in-depth analysis of the technology and its implications for the future of mobile devices.",
        featuredImage: "https://images.unsplash.com/photo-1551739440-5dd934d3a94a?q=80&w=400&h=225&auto=format&fit=crop",
        featured: false,
        readTime: 6,
      },
      {
        title: "DeFi: How Decentralized Finance is Challenging Banks",
        slug: "defi-challenging-banks",
        excerpt: "Explore how blockchain-based decentralized finance platforms are offering alternatives to traditional banking services and investments.",
        content: "Decentralized Finance (DeFi) is emerging as a serious alternative to traditional financial services. By leveraging blockchain technology, DeFi platforms can offer lending, borrowing, and investment services without intermediaries. This article explores the growth of DeFi and its potential to disrupt conventional banking models.",
        featuredImage: "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?q=80&w=400&h=225&auto=format&fit=crop",
        featured: false,
        readTime: 8,
      },
      {
        title: "The Future of Manufacturing: Robotic Workforces",
        slug: "future-manufacturing-robotic-workforces",
        excerpt: "How advanced robotics and AI are transforming manufacturing floors and changing the nature of industrial work forever.",
        content: "Manufacturing is undergoing a profound transformation with the integration of advanced robotics and artificial intelligence. These technologies are not only increasing efficiency and reducing costs but also changing the very nature of industrial work. This article examines the latest innovations and their implications for workers, businesses, and economies.",
        featuredImage: "https://images.unsplash.com/photo-1597388417886-188a49c267a6?q=80&w=400&h=225&auto=format&fit=crop",
        featured: false,
        readTime: 7,
      },
      {
        title: "Meta's New VR Headset Sets New Standard for Immersive Computing",
        slug: "meta-vr-headset-immersive-computing",
        excerpt: "Meta's latest VR device promises to blur the lines between virtual and physical reality with groundbreaking display technology.",
        content: "Meta's newest virtual reality headset represents a significant leap forward in immersive computing technology. With improvements in display resolution, field of view, and haptic feedback, the experience of virtual reality is becoming increasingly indistinguishable from physical reality. This article explores the technical innovations and potential applications of this groundbreaking device.",
        featuredImage: "https://images.unsplash.com/photo-1523961131990-5ea7c61b2107?q=80&w=400&h=225&auto=format&fit=crop",
        featured: false,
        readTime: 5,
      },
    ];
    
    // Add posts to each category
    defaultPosts.forEach((post, index) => {
      // Determine category and author for each post
      let categoryId;
      if (index === 0 || index === 3 || index === 6) {
        categoryId = 1; // Finance
      } else if (index === 1 || index === 4 || index === 7) {
        categoryId = 2; // Automation
      } else {
        categoryId = 3; // Tech News
      }
      
      const authorId = (index % 6) + 1;
      
      this.createPost({
        ...post,
        categoryId,
        authorId,
      });
    });
    
    // Initialize trending topics
    const defaultTopics = [
      { name: "Cryptocurrency", slug: "cryptocurrency" },
      { name: "Artificial Intelligence", slug: "artificial-intelligence" },
      { name: "Machine Learning", slug: "machine-learning" },
      { name: "Blockchain", slug: "blockchain" },
      { name: "Cybersecurity", slug: "cybersecurity" },
      { name: "5G", slug: "5g" },
      { name: "Cloud Computing", slug: "cloud-computing" },
      { name: "IoT", slug: "iot" },
      { name: "Startup", slug: "startup" },
      { name: "Tech Giants", slug: "tech-giants" },
    ];
    
    defaultTopics.forEach(topic => this.createTopic(topic));
  }

  // User methods
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.userId++;
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }
  
  // Category methods
  async getAllCategories(): Promise<Category[]> {
    return Array.from(this.categories.values());
  }
  
  async getCategoryBySlug(slug: string): Promise<Category | undefined> {
    return Array.from(this.categories.values()).find(
      (category) => category.slug === slug,
    );
  }
  
  async createCategory(insertCategory: InsertCategory): Promise<Category> {
    const id = this.categoryId++;
    const category: Category = { ...insertCategory, id };
    this.categories.set(id, category);
    return category;
  }
  
  // Post methods
  async getAllPosts(): Promise<Post[]> {
    return Array.from(this.posts.values()).sort(
      (a, b) => new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime()
    );
  }
  
  async getFeaturedPosts(): Promise<Post[]> {
    return Array.from(this.posts.values())
      .filter(post => post.featured)
      .sort((a, b) => new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime());
  }
  
  async getPostsByCategory(categoryId: number): Promise<Post[]> {
    return Array.from(this.posts.values())
      .filter(post => post.categoryId === categoryId)
      .sort((a, b) => new Date(b.publishDate).getTime() - new Date(a.publishDate).getTime());
  }
  
  async getPostsByCategorySlug(slug: string): Promise<Post[]> {
    const category = await this.getCategoryBySlug(slug);
    if (!category) return [];
    
    return this.getPostsByCategory(category.id);
  }
  
  async getPostBySlug(slug: string): Promise<Post | undefined> {
    return Array.from(this.posts.values()).find(
      (post) => post.slug === slug,
    );
  }
  
  async createPost(insertPost: InsertPost): Promise<Post> {
    const id = this.postId++;
    const now = new Date();
    const post: Post = { 
      ...insertPost, 
      id,
      publishDate: now
    };
    this.posts.set(id, post);
    return post;
  }
  
  // Author methods
  async getAllAuthors(): Promise<Author[]> {
    return Array.from(this.authors.values());
  }
  
  async getAuthor(id: number): Promise<Author | undefined> {
    return this.authors.get(id);
  }
  
  async createAuthor(insertAuthor: InsertAuthor): Promise<Author> {
    const id = this.authorId++;
    const author: Author = { ...insertAuthor, id };
    this.authors.set(id, author);
    return author;
  }
  
  // Topic methods
  async getAllTopics(): Promise<Topic[]> {
    return Array.from(this.topics.values());
  }
  
  async createTopic(insertTopic: InsertTopic): Promise<Topic> {
    const id = this.topicId++;
    const topic: Topic = { ...insertTopic, id };
    this.topics.set(id, topic);
    return topic;
  }
}

export const storage = new MemStorage();
