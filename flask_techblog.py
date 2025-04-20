from flask import Flask, render_template, request, redirect, url_for, flash, abort
from datetime import datetime
import markdown
import os

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-testing'

# In-memory data storage
categories = [
    {
        'id': 1,
        'name': 'Finance',
        'slug': 'finance',
        'description': 'The latest in fintech, crypto, and personal finance.',
        'color': '#4CAF50'
    },
    {
        'id': 2,
        'name': 'Automation',
        'slug': 'automation',
        'description': 'Smart home, robotics, and AI automation tools.',
        'color': '#2196F3'
    },
    {
        'id': 3,
        'name': 'Tech News',
        'slug': 'tech-news',
        'description': 'Breaking tech news and product releases.',
        'color': '#9C27B0'
    }
]

authors = [
    {
        'id': 1,
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'bio': 'Tech enthusiast and finance expert',
        'avatar': '/static/images/avatars/avatar-1.jpg'
    },
    {
        'id': 2,
        'name': 'John Smith',
        'email': 'john@example.com',
        'bio': 'AI researcher and smart home consultant',
        'avatar': '/static/images/avatars/avatar-2.jpg'
    }
]

topics = [
    {'id': 1, 'name': 'Cryptocurrency', 'slug': 'cryptocurrency'},
    {'id': 2, 'name': 'Blockchain', 'slug': 'blockchain'},
    {'id': 3, 'name': 'Smart Home', 'slug': 'smart-home'},
    {'id': 4, 'name': 'AI', 'slug': 'ai'},
    {'id': 5, 'name': 'Machine Learning', 'slug': 'machine-learning'},
    {'id': 6, 'name': 'Apple', 'slug': 'apple'},
    {'id': 7, 'name': 'Google', 'slug': 'google'},
    {'id': 8, 'name': 'Microsoft', 'slug': 'microsoft'}
]

posts = [
    {
        'id': 1,
        'title': 'The Future of Cryptocurrency in Banking',
        'slug': 'future-cryptocurrency-banking',
        'excerpt': 'How cryptocurrencies are changing the traditional banking landscape and what this means for consumers.',
        'content': '''
Cryptocurrencies have been gaining significant traction in recent years, challenging the traditional banking system in unprecedented ways. Financial institutions that once dismissed digital currencies are now exploring ways to integrate them into their services.

Major banks are starting to offer cryptocurrency custody services, allowing customers to buy, sell, and hold digital assets. This shift represents a significant departure from their previous stance and acknowledges the growing demand for crypto-related services.

The rise of decentralized finance (DeFi) platforms also presents both challenges and opportunities for traditional banks. These platforms offer financial services without intermediaries, potentially disrupting the banking sector's long-established business models.

Central Bank Digital Currencies (CBDCs) are another important development, with many countries actively researching or piloting their own digital currencies. These government-backed digital currencies could potentially combine the innovations of cryptocurrency with the stability and trust of traditional fiat currencies.

As these technologies continue to evolve, we can expect further integration between cryptocurrency and traditional banking, ultimately creating a more diverse and accessible financial ecosystem for users worldwide.
        ''',
        'publish_date': datetime(2025, 4, 15),
        'read_time': 7,
        'featured': True,
        'featured_image': '/static/images/posts/crypto-banking.jpg',
        'category_id': 1,
        'author_id': 1,
        'topic_ids': [1, 2]
    },
    {
        'id': 2,
        'title': 'AI-Powered Home Automation in 2025',
        'slug': 'ai-powered-home-automation',
        'excerpt': 'The latest advancements in AI-driven home automation systems and how they're transforming daily life.',
        'content': '''
Home automation has come a long way from simple programmable thermostats and light timers. Today's AI-powered smart home systems can learn from your behaviors, anticipate your needs, and seamlessly coordinate multiple devices to enhance comfort, convenience, and efficiency.

Modern AI assistants like Google Home, Amazon Alexa, and Apple HomePod have evolved beyond basic voice commands to become the central nervous system of the smart home. These systems now employ sophisticated machine learning algorithms that improve over time, becoming more responsive to your specific preferences and patterns.

Energy management is one area where AI is making a significant impact. Smart thermostats don't just follow pre-set schedules anymore; they analyze your usage patterns, weather forecasts, and even the thermal characteristics of your home to optimize heating and cooling for both comfort and energy savings.

Security systems have become more intelligent as well. AI-powered cameras can distinguish between normal activity and potential threats, reducing false alarms while providing more reliable protection. Some systems can even recognize familiar faces and alert you when strangers approach your home.

The kitchen is another frontier for smart home innovation. Refrigerators can track inventory and suggest recipes based on available ingredients, while smart ovens can automatically adjust cooking parameters for perfect results. Some systems can even coordinate multiple appliances to ensure all components of a meal are ready at the same time.

As we look toward 2025 and beyond, the integration of AI into home automation will continue to deepen. Expect to see more predictive capabilities, greater interoperability between devices from different manufacturers, and smarter energy management across all systems.
        ''',
        'publish_date': datetime(2025, 4, 10),
        'read_time': 8,
        'featured': True,
        'featured_image': '/static/images/posts/smart-home.jpg',
        'category_id': 2,
        'author_id': 2,
        'topic_ids': [3, 4]
    },
    {
        'id': 3,
        'title': "Apple's New M3 Chip: A Quantum Leap in Computing",
        'slug': 'apple-m3-chip-quantum-leap',
        'excerpt': "An in-depth look at Apple's latest M3 chip architecture and its performance improvements over previous generations.",
        'content': '''
Apple's new M3 chip represents a significant advancement in computer processing technology, building upon the already impressive foundation established by the M1 and M2 series. This latest generation of Apple Silicon introduces several architectural improvements that deliver substantial gains in performance, efficiency, and capabilities.

At the heart of the M3's improvements is the transition to a more advanced manufacturing process. While the M1 and M2 chips were built on a 5nm process, the M3 utilizes a 3nm process technology. This smaller process node allows for greater transistor density, improved power efficiency, and higher performance potential.

The CPU in the M3 maintains Apple's hybrid architecture with both performance and efficiency cores, but with notable enhancements to both types. The performance cores feature improved branch prediction, wider execution units, and larger caches, allowing for faster processing of complex tasks.

The GPU in the M3 has received perhaps the most substantial upgrade. It now supports hardware-accelerated ray tracing and mesh shading, technologies previously only available in high-end desktop graphics cards. This brings significantly improved graphics capabilities to Apple's devices, enabling more realistic lighting, shadows, and reflections in games and professional applications.

The Neural Engine, Apple's dedicated hardware for machine learning tasks, has also been enhanced in the M3. It now processes up to 40 trillion operations per second, making on-device AI faster and more efficient. This accelerates everything from photo processing to voice recognition and augmented reality applications.

Memory bandwidth has been significantly increased in the M3, with a wider memory bus and support for faster LPDDR5 RAM. This allows for quicker data transfer between the CPU, GPU, and system memory, reducing bottlenecks in data-intensive workflows.

Perhaps most impressive is the M3's power efficiency. Despite the performance gains, the chip maintains or even improves upon the exceptional battery life that has become a hallmark of Apple Silicon. This allows devices like MacBooks to deliver workstation-level performance while maintaining all-day battery life.

Early benchmarks suggest that the M3 represents a 20-30% increase in CPU performance and up to a 40% increase in GPU performance compared to the M2, depending on the specific task. These gains are particularly notable in areas like video editing, 3D rendering, and machine learning, where the architectural improvements have the most impact.

The introduction of the M3 chip cements Apple's position as a leader in silicon design and continues the company's successful transition away from Intel processors. As developers continue to optimize their software for Apple Silicon, users can expect even greater performance and capabilities from their M3-powered devices in the future.
        ''',
        'publish_date': datetime(2025, 4, 5),
        'read_time': 10,
        'featured': True,
        'featured_image': '/static/images/posts/apple-chip.jpg',
        'category_id': 3,
        'author_id': 1,
        'topic_ids': [6]
    }
]

# Add more simulated posts
posts.extend([
    {
        'id': 4,
        'title': 'Blockchain Beyond Cryptocurrency: Enterprise Applications',
        'slug': 'blockchain-beyond-cryptocurrency',
        'excerpt': 'How blockchain technology is being used for supply chain tracking, digital identity, and more beyond just cryptocurrencies.',
        'content': 'Detailed content about blockchain applications in enterprise...',
        'publish_date': datetime(2025, 4, 2),
        'read_time': 6,
        'featured': False,
        'featured_image': '/static/images/posts/blockchain.jpg',
        'category_id': 1,
        'author_id': 1,
        'topic_ids': [2]
    },
    {
        'id': 5,
        'title': 'The Rise of Robotic Process Automation in Finance',
        'slug': 'rise-rpa-finance',
        'excerpt': 'How RPA is transforming financial operations by automating routine tasks and improving efficiency.',
        'content': 'Detailed content about RPA in financial operations...',
        'publish_date': datetime(2025, 3, 28),
        'read_time': 5,
        'featured': False,
        'featured_image': '/static/images/posts/rpa.jpg',
        'category_id': 2,
        'author_id': 2,
        'topic_ids': [4, 5]
    },
    {
        'id': 6,
        'title': 'Quantum Computing: A New Era for Technology',
        'slug': 'quantum-computing-new-era',
        'excerpt': 'An introduction to quantum computing and how it will revolutionize computational capabilities.',
        'content': 'Detailed content about quantum computing advancements...',
        'publish_date': datetime(2025, 3, 25),
        'read_time': 9,
        'featured': False,
        'featured_image': '/static/images/posts/quantum.jpg',
        'category_id': 3,
        'author_id': 1,
        'topic_ids': [7, 8]
    }
])

# Helper functions to simulate database queries
def get_category_by_id(category_id):
    return next((category for category in categories if category['id'] == category_id), None)

def get_category_by_slug(slug):
    return next((category for category in categories if category['slug'] == slug), None)

def get_author_by_id(author_id):
    return next((author for author in authors if author['id'] == author_id), None)

def get_topic_by_id(topic_id):
    return next((topic for topic in topics if topic['id'] == topic_id), None)

def get_topic_by_slug(slug):
    return next((topic for topic in topics if topic['slug'] == slug), None)

def get_post_by_slug(slug):
    return next((post for post in posts if post['slug'] == slug), None)

def get_posts_by_category_id(category_id):
    return [post for post in posts if post['category_id'] == category_id]

def get_featured_posts():
    return [post for post in posts if post['featured']]

def get_posts_by_topic_id(topic_id):
    return [post for post in posts if topic_id in post['topic_ids']]

# Enhance posts with related objects
def enhance_post(post):
    enhanced_post = dict(post)
    enhanced_post['category'] = get_category_by_id(post['category_id'])
    enhanced_post['author'] = get_author_by_id(post['author_id'])
    enhanced_post['topics'] = [get_topic_by_id(topic_id) for topic_id in post['topic_ids']]
    return enhanced_post

# Context processors
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_categories():
    return {'categories': categories}

# Routes
@app.route('/')
def home():
    featured_posts = [enhance_post(post) for post in get_featured_posts()]
    latest_posts = [enhance_post(post) for post in sorted(posts, key=lambda x: x['publish_date'], reverse=True)[:6]]
    trending_topics = topics[:8]
    return render_template('home.html', 
                           featured_posts=featured_posts, 
                           categories=categories, 
                           latest_posts=latest_posts, 
                           trending_topics=trending_topics)

@app.route('/category/<slug>')
def category(slug):
    category = get_category_by_slug(slug)
    if not category:
        abort(404)
    category_posts = get_posts_by_category_id(category['id'])
    posts_enhanced = [enhance_post(post) for post in category_posts]
    trending_topics = topics[:8]
    return render_template('category.html', 
                           category=category, 
                           posts=posts_enhanced, 
                           trending_topics=trending_topics)

@app.route('/post/<slug>')
def post(slug):
    post = get_post_by_slug(slug)
    if not post:
        abort(404)
    enhanced_post = enhance_post(post)
    enhanced_post['content_html'] = markdown.markdown(post['content'])
    trending_topics = topics[:8]
    return render_template('post.html', 
                           post=enhanced_post, 
                           trending_topics=trending_topics)

@app.route('/topic/<slug>')
def topic(slug):
    topic = get_topic_by_slug(slug)
    if not topic:
        abort(404)
    topic_posts = get_posts_by_topic_id(topic['id'])
    posts_enhanced = [enhance_post(post) for post in topic_posts]
    return render_template('topic.html', 
                           topic=topic, 
                           posts=posts_enhanced)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Create placeholder images for avatars and posts
def create_placeholder_images():
    avatar_dir = os.path.join(app.static_folder, 'images/avatars')
    posts_dir = os.path.join(app.static_folder, 'images/posts')
    
    # Ensure directories exist
    os.makedirs(avatar_dir, exist_ok=True)
    os.makedirs(posts_dir, exist_ok=True)
    
    # Create avatar placeholders
    for i in range(1, 3):
        avatar_file = os.path.join(avatar_dir, f'avatar-{i}.jpg')
        if not os.path.exists(avatar_file):
            with open(avatar_file, 'w') as f:
                f.write('placeholder')
    
    # Create post image placeholders
    post_images = ['crypto-banking.jpg', 'smart-home.jpg', 'apple-chip.jpg', 
                  'blockchain.jpg', 'rpa.jpg', 'quantum.jpg']
    
    for img in post_images:
        post_file = os.path.join(posts_dir, img)
        if not os.path.exists(post_file):
            with open(post_file, 'w') as f:
                f.write('placeholder')

# Initialize placeholder images
create_placeholder_images()

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)