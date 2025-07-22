from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import markdown
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Add these imports at the top of your Flask app (after existing imports)
import subprocess
import threading
import json
import webbrowser
from datetime import datetime
import pendulum as dt
import os
import signal
import psutil
import time
import sys




# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///techblog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Context processors
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_categories():
    return {'categories': Category.query.all()}

# Define models
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    color = db.Column(db.String(20))
    posts = db.relationship('Post', backref='category', lazy=True)

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(200))
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_time = db.Column(db.Integer, default=5)
    featured = db.Column(db.Boolean, default=False)
    featured_image = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False)
    topics = db.relationship('Topic', secondary='post_topics', backref=db.backref('posts', lazy='dynamic'))

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)

class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    subscribed_on = db.Column(db.DateTime, default=datetime.utcnow)

# Association table for Post and Topic many-to-many relationship
post_topics = db.Table('post_topics',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id'), primary_key=True)
)





# Global variables for trading state
TRADING_STATE_FILE = '/home/siddartha1192/blogging/trading_state.txt'
TRADING_LOG_FILE = '/home/siddartha1192/blogging/trading_execution.log'

# Trading configuration (you can modify these)
CLIENT_ID = 'V9GQM61IVI-100'  # Your client ID
SECRET_KEY = '3OH8C9ELBB'     # Your secret key
REDIRECT_URI = 'https://127.0.0.1:5000/login'

def read_trading_state():
    """Read current trading state from file"""
    try:
        if os.path.exists(TRADING_STATE_FILE):
            with open(TRADING_STATE_FILE, 'r') as f:
                return json.load(f)
        else:
            return {
                'access_token': None,
                'token_date': None,
                'trading_active': 'false',
                'process_id': None,
                'last_started': None,
                'last_stopped': None,
                'script_status': 'stopped'
            } 
    except Exception as e:
        return {
            'access_token': None,
            'token_date': None,
            'trading_active': 'false',
            'process_id': None,
            'last_started': None,
            'last_stopped': None,
            'script_status': 'error',
            'error': str(e)
        }

def write_trading_state(state):
    """Write trading state to file"""
    try:
        with open(TRADING_STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        return True
    except Exception as e:
        return False

def log_trading_event(message):
    """Log trading events to file"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(TRADING_LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - {message}\n")
    except:
        pass


# Routes
@app.route('/')
def home():
    featured_posts = Post.query.filter_by(featured=True).order_by(Post.publish_date.desc()).all()
    categories = Category.query.all()
    latest_posts = Post.query.order_by(Post.publish_date.desc()).limit(6).all()
    trending_topics = Topic.query.limit(8).all()
    return render_template('home.html', 
                           featured_posts=featured_posts, 
                           categories=categories, 
                           latest_posts=latest_posts, 
                           trending_topics=trending_topics)







@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        # Return JSON error if it's an AJAX call
        if request.is_json:
            return jsonify({'status': 'danger', 'message': 'Please provide a valid email.'}), 400
        flash('Please provide a valid email.', 'danger')
        return redirect(request.referrer or url_for('home'))

    existing = Subscriber.query.filter_by(email=email).first()
    if existing:
        if request.is_json:
            return jsonify({'status': 'warning', 'message': 'You are already subscribed!'}), 200
        flash('You are already subscribed!', 'warning')
    else:
        new_sub = Subscriber(email=email)
        db.session.add(new_sub)
        db.session.commit()
        if request.is_json:
            return jsonify({'status': 'success', 'message': 'Subscription successful!'}), 200
        flash('Subscription successful!', 'success')

    return redirect(request.referrer or url_for('home'))

@app.route('/ads.txt')
def serve_ads_txt():
    # Use 'with' to automatically close the file after reading
    with open('static/ads.txt', 'r') as adFile:
        return adFile.read()

@app.route('/category/<slug>')
def category(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    posts = Post.query.filter_by(category_id=category.id).order_by(Post.publish_date.desc()).all()
    trending_topics = Topic.query.limit(8).all()
    return render_template('category.html', 
                           category=category, 
                           posts=posts, 
                           trending_topics=trending_topics)

@app.route('/post/<slug>')
def post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    post.content_html = markdown.markdown(post.content)
    trending_topics = Topic.query.limit(8).all()
    return render_template('post.html', 
                           post=post, 
                           trending_topics=trending_topics)


@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('home'))
    post = Post.query.filter(Post.title.contains(query) | Post.content.contains(query)).all()
    return render_template('search.html', topic=query, posts=post)


@app.route('/topic/<slug>')
def topic(slug):
    topic = Topic.query.filter_by(slug=slug).first_or_404()
    posts = topic.posts.order_by(Post.publish_date.desc()).all()
    return render_template('topic.html', 
                           topic=topic, 
                           posts=posts)

@app.route('/about')
def about():
    return render_template('about.html')

# Helper function to initialize the database with sample data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Only add sample data if the database is empty
        if Category.query.count() == 0:
            # Create categories
            finance = Category(
                name="Finance", 
                slug="finance", 
                description="The latest in fintech, crypto, and personal finance.", 
                color="#4CAF50"
            )
            automation = Category(
                name="Automation", 
                slug="automation", 
                description="Smart home, robotics, and AI automation tools.", 
                color="#2196F3"
            )
            tech_news = Category(
                name="Tech News", 
                slug="tech-news", 
                description="Breaking tech news and product releases.", 
                color="#9C27B0"
            )
            
            db.session.add_all([finance, automation, tech_news])
            db.session.commit()
            
            # Create authors
            author1 = Author(
                name="Jane Doe", 
                email="jane@example.com", 
                bio="Tech enthusiast and finance expert", 
                avatar="/static/images/avatars/avatar-1.svg"
            )
            author2 = Author(
                name="John Smith", 
                email="john@example.com", 
                bio="AI researcher and smart home consultant", 
                avatar="/static/images/avatars/avatar-2.svg"
            )
            
            db.session.add_all([author1, author2])
            db.session.commit()
            
            # Create topics
            topics = [
                Topic(name="Cryptocurrency", slug="cryptocurrency"),
                Topic(name="Blockchain", slug="blockchain"),
                Topic(name="Smart Home", slug="smart-home"),
                Topic(name="AI", slug="ai"),
                Topic(name="Machine Learning", slug="machine-learning"),
                Topic(name="Apple", slug="apple"),
                Topic(name="Google", slug="google"),
                Topic(name="Microsoft", slug="microsoft")
            ]
            
            db.session.add_all(topics)
            db.session.commit()
            
            # Create posts
            posts = [
                Post(
                    title="The Future of Cryptocurrency in Banking",
                    slug="future-cryptocurrency-banking",
                    excerpt="How cryptocurrencies are changing the traditional banking landscape and what this means for consumers.",
                    content="""
Cryptocurrencies have been gaining significant traction in recent years, challenging the traditional banking system in unprecedented ways. Financial institutions that once dismissed digital currencies are now exploring ways to integrate them into their services.

Major banks are starting to offer cryptocurrency custody services, allowing customers to buy, sell, and hold digital assets. This shift represents a significant departure from their previous stance and acknowledges the growing demand for crypto-related services.

The rise of decentralized finance (DeFi) platforms also presents both challenges and opportunities for traditional banks. These platforms offer financial services without intermediaries, potentially disrupting the banking sector's long-established business models.

Central Bank Digital Currencies (CBDCs) are another important development, with many countries actively researching or piloting their own digital currencies. These government-backed digital currencies could potentially combine the innovations of cryptocurrency with the stability and trust of traditional fiat currencies.

As these technologies continue to evolve, we can expect further integration between cryptocurrency and traditional banking, ultimately creating a more diverse and accessible financial ecosystem for users worldwide.
                    """,
                    read_time=7,
                    featured=True,
                    featured_image="/static/images/posts/crypto-banking.svg",
                    category_id=1,  # Finance
                    author_id=1,  # Jane Doe
                ),
                Post(
                    title="AI-Powered Home Automation in 2025",
                    slug="ai-powered-home-automation",
                    excerpt="The latest advancements in AI-driven home automation systems and how they're transforming daily life.",
                    content="""
Home automation has come a long way from simple programmable thermostats and light timers. Today's AI-powered smart home systems can learn from your behaviors, anticipate your needs, and seamlessly coordinate multiple devices to enhance comfort, convenience, and efficiency.

Modern AI assistants like Google Home, Amazon Alexa, and Apple HomePod have evolved beyond basic voice commands to become the central nervous system of the smart home. These systems now employ sophisticated machine learning algorithms that improve over time, becoming more responsive to your specific preferences and patterns.

Energy management is one area where AI is making a significant impact. Smart thermostats don't just follow pre-set schedules anymore; they analyze your usage patterns, weather forecasts, and even the thermal characteristics of your home to optimize heating and cooling for both comfort and energy savings.

Security systems have become more intelligent as well. AI-powered cameras can distinguish between normal activity and potential threats, reducing false alarms while providing more reliable protection. Some systems can even recognize familiar faces and alert you when strangers approach your home.

The kitchen is another frontier for smart home innovation. Refrigerators can track inventory and suggest recipes based on available ingredients, while smart ovens can automatically adjust cooking parameters for perfect results. Some systems can even coordinate multiple appliances to ensure all components of a meal are ready at the same time.

As we look toward 2025 and beyond, the integration of AI into home automation will continue to deepen. Expect to see more predictive capabilities, greater interoperability between devices from different manufacturers, and smarter energy management across all systems.
                    """,
                    read_time=8,
                    featured=True,
                    featured_image="/static/images/posts/smart-home.svg",
                    category_id=2,  # Automation
                    author_id=2,  # John Smith
                ),
                Post(
                    title="Apple's New M3 Chip: A Quantum Leap in Computing",
                    slug="apple-m3-chip-quantum-leap",
                    excerpt="An in-depth look at Apple's latest M3 chip architecture and its performance improvements over previous generations.",
                    content="""
Apple's new M3 chip represents a significant advancement in computer processing technology, building upon the already impressive foundation established by the M1 and M2 series. This latest generation of Apple Silicon introduces several architectural improvements that deliver substantial gains in performance, efficiency, and capabilities.

At the heart of the M3's improvements is the transition to a more advanced manufacturing process. While the M1 and M2 chips were built on a 5nm process, the M3 utilizes a 3nm process technology. This smaller process node allows for greater transistor density, improved power efficiency, and higher performance potential.

The CPU in the M3 maintains Apple's hybrid architecture with both performance and efficiency cores, but with notable enhancements to both types. The performance cores feature improved branch prediction, wider execution units, and larger caches, allowing for faster processing of complex tasks. Meanwhile, the efficiency cores have been optimized to handle everyday tasks while consuming even less power than before.

GPU performance sees perhaps the most dramatic improvement in the M3. Apple has redesigned the graphics architecture to support hardware-accelerated ray tracing and mesh shading—technologies that enable more realistic lighting, shadows, and reflections in games and professional 3D applications. The GPU also features dynamic caching, which allocates memory more efficiently based on the needs of the current workload.

The Neural Engine, responsible for machine learning tasks, has been enhanced to process more operations per second, enabling faster and more complex AI features. This improvement supports everything from more accurate voice recognition to sophisticated image processing capabilities.

Memory bandwidth has also increased, with the M3 featuring a more advanced memory subsystem that can move data between the CPU, GPU, and other components more quickly. This reduces bottlenecks when working with large files or complex applications.

For professionals, perhaps the most welcome improvement is enhanced external display support. The M3 can drive multiple high-resolution displays simultaneously, making it better suited for complex workstation setups used in fields like video editing, 3D modeling, and software development.

Battery efficiency continues to be a standout feature of Apple Silicon, and the M3 pushes this advantage even further. Early benchmarks suggest that M3-equipped MacBooks can achieve even longer battery life than their predecessors while delivering better performance—a combination that was once thought impossible in mobile computing.
                    """,
                    read_time=10,
                    featured=True,
                    featured_image="/static/images/posts/apple-chip.svg",
                    category_id=3,  # Tech News
                    author_id=1,  # Jane Doe
                ),
                Post(
                    title="Blockchain Technology Beyond Cryptocurrency",
                    slug="blockchain-beyond-cryptocurrency",
                    excerpt="Exploring how blockchain technology is being used in supply chain management, healthcare, and more.",
                    content="""
While blockchain technology gained initial fame as the foundation for cryptocurrencies like Bitcoin, its potential applications extend far beyond digital currencies. The fundamental properties of blockchain—decentralization, immutability, and transparency—make it valuable for numerous industries seeking more secure and efficient ways to manage data and transactions.

In supply chain management, blockchain provides an unprecedented level of transparency and traceability. Companies like Walmart and Maersk are already implementing blockchain systems to track products from origin to consumer. This allows for quicker identification of contaminated food sources during recalls, verification of sustainable and ethical sourcing claims, and reduction in counterfeit products entering the market.

Healthcare is another sector benefiting from blockchain innovation. Medical records stored on blockchain can be securely shared between providers while maintaining patient privacy and control. Prescription drug tracking on blockchain can help combat the opioid crisis and reduce counterfeit medications. Additionally, blockchain can streamline clinical trials by providing transparent, tamper-proof records of trial data.

The real estate industry is using blockchain to simplify property transactions and title management. By recording property ownership on a blockchain, the process of verifying titles becomes faster and more reliable, potentially reducing the need for title insurance and speeding up closing times for property sales.

Voting systems built on blockchain could potentially increase election security and transparency. While still largely experimental, blockchain voting platforms could provide verifiable records of votes while maintaining voter privacy, potentially increasing public trust in election outcomes.

Intellectual property management is also being transformed by blockchain. Creative works can be timestamped and recorded on blockchain, establishing proof of ownership and enabling more direct compensation models for creators through smart contracts.

These diverse applications illustrate how blockchain technology is evolving beyond its cryptocurrency origins to address fundamental challenges across multiple industries. As the technology matures and becomes more scalable and energy-efficient, we can expect even broader adoption and innovation in the coming years.
                    """,
                    read_time=6,
                    featured=False,
                    featured_image="/static/images/posts/blockchain.svg",
                    category_id=1,  # Finance
                    author_id=2,  # John Smith
                ),
                Post(
                    title="Siddartha testing Blog",
                    slug="test-blog",
                    excerpt="My First Blog on Flask App",
                    content="""
Siddartha testing blog. 

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bash Script Code Showcase</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.0/themes/prism.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.0/components/prism-bash.min.js"></script>
    <style>

        .code-box {
            position: relative;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
            overflow: auto;
        }

        .copy-button {
            background-color: #0074d9;
            color: #fff;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            position: absolute;
            top: 10px;
            right: 10px;
        }

        .copy-button.copied {
            background-color: #4CAF50;
            transition: background-color 0.5s;
        }
    </style>
</head>
<body>
    <div class="code-box">
        <button class="copy-button" onclick="copyToClipboard(0)">Copy Code</button>
        <pre><code class="language-bash">
from fyers_apiv3.FyersWebsocket import data_ws
import time
import pandas as pd
from fyers_apiv3 import fyersModel
import os
fyers = fyersModel.FyersModel(token=’token’,is_async=False,client_id='VXXXXXXXI-100',log_path="")


def onmessage(message):
    print("Response:", message['ltp'])
    ReferencePrice = int(get_ltp(client_id,access_token,'NSE:NIFTYBANK-INDEX'))
    ltp = message['ltp']
    symbol='NSE:NIFTYBANK-INDEX'
    allPositions = fyers.positions()['netPositions']
    current_position_side = get_openposition_side(allPositions)
    buy_sell_status = check_price_level(client_id,access_token,symbol,ReferencePrice)

    if buy_sell_status == 'buy' and current_position_side != 'CE':
        if ([obj for obj in allPositions if obj["netQty"] > 0]):
            close_all_positions(client_id, access_token)
        else:
            print('')
        buy_symbol = current_BN_ATM_CE()
        place_market_order(client_id,access_token,buy_symbol,1,15)

    elif buy_sell_status == 'sell' and current_position_side != 'PE':
        if ([obj for obj in allPositions if obj["netQty"] > 0]):
            close_all_positions(client_id, access_token)
        else:
            print('')
        sell_symbol = current_BN_ATM_PE()
        place_market_order(client_id,access_token,sell_symbol,1,15)

    else:
        print("Waiting for correct price.")
    check_total_PNL()
    time.sleep(30)


def onerror(message):
    print("Error:", message)


def onclose(message):
    print("Connection closed:", message)


def onopen():
    data_type = "SymbolUpdate"
    symbols = ['NSE:NIFTYBANK-INDEX']
    fyers1.subscribe(symbols=symbols, data_type=data_type)
    fyers1.keep_running()

access_token_data = ‘XXXXXXX-100:' + access_token
# Create a FyersDataSocket instance with the provided parameters
fyers1 = data_ws.FyersDataSocket(
    access_token=access_token_data,
    log_path="",
    litemode=True,
    write_to_file=False,
    reconnect=True,
    on_connect=onopen,
    on_close=onclose,
    on_error=onerror,
    on_message=onmessage
)
# Establish a connection to the Fyers WebSocket
fyers1.connect()
      </code></pre>
    </div>

    <script>
        Prism.highlightAll();

        function copyToClipboard(index) {
            const codeBlocks = document.querySelectorAll('.code-box code');
            const selectedCode = codeBlocks[index].textContent;
            const button = document.querySelectorAll('.copy-button')[index];
            
            const textarea = document.createElement('textarea');
            textarea.value = selectedCode;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);

            // Add the 'copied' class to change button color temporarily
            button.classList.add('copied');
            setTimeout(function() {
                button.classList.remove('copied');
            }, 500);
        }
    </script>
</body>
</html>


Robotic Process Automation (RPA) is revolutionizing how businesses handle routine, rule-based tasks that once required significant human effort. By deploying software robots or "bots" that can mimic human interactions with digital systems, organizations are achieving new levels of efficiency, accuracy, and scalability in their operations.

Unlike physical robots on assembly lines, RPA bots are software programs that work with existing computer systems. They can log into applications, enter data, complete forms, extract information from documents, and perform calculations—all according to predefined rules. This makes them perfect for handling repetitive, high-volume tasks that follow consistent patterns.

Finance departments have been early adopters of RPA, using bots for accounts payable processing, reconciliations, and financial reporting. A bot can extract invoice data, verify it against purchase orders and receipts, update accounting systems, and even flag exceptions for human review—all without manual intervention for standard cases.

Human resources is another area seeing significant RPA implementation. Bots can streamline employee onboarding by automatically creating accounts across multiple systems, processing paperwork, and ensuring compliance requirements are met. They can also assist with payroll processing, benefits administration, and routine employee queries.

Customer service operations benefit from RPA through faster processing of standard requests. Bots can retrieve customer information across multiple systems, update records, process simple requests, and route complex issues to the appropriate human agents with all relevant information already gathered.

While RPA offers clear advantages in efficiency and accuracy, its impact on employment remains a complex issue. Some routine positions may be eliminated as tasks are automated, but new roles are also emerging to design, implement, and oversee RPA systems. Many organizations are retraining employees to handle more complex, judgment-intensive work while delegating routine tasks to bots.

The most successful RPA implementations tend to focus on augmenting human capabilities rather than replacing workers entirely. By handling repetitive, time-consuming tasks, bots free up employees to focus on activities that require creativity, emotional intelligence, and complex decision-making—areas where humans still maintain a significant advantage over automation.

As RPA technology continues to evolve, particularly through integration with artificial intelligence, its capabilities will extend beyond simple rule-based tasks to more complex processes requiring judgment and adaptation. This progression will likely accelerate the transformation of work across many industries in the coming years.
                    """,
                    read_time=7,
                    featured=False,
                    featured_image="/static/images/posts/rpa.svg",
                    category_id=2,  # Automation
                    author_id=1,  # Jane Doe
                ),                
                Post(
                    title="Robotic Process Automation in the Workplace",
                    slug="robotic-process-automation-workplace",
                    excerpt="How RPA is transforming office work and what it means for the future of employment.",
                    content="""
Robotic Process Automation (RPA) is revolutionizing how businesses handle routine, rule-based tasks that once required significant human effort. By deploying software robots or "bots" that can mimic human interactions with digital systems, organizations are achieving new levels of efficiency, accuracy, and scalability in their operations.

Unlike physical robots on assembly lines, RPA bots are software programs that work with existing computer systems. They can log into applications, enter data, complete forms, extract information from documents, and perform calculations—all according to predefined rules. This makes them perfect for handling repetitive, high-volume tasks that follow consistent patterns.

Finance departments have been early adopters of RPA, using bots for accounts payable processing, reconciliations, and financial reporting. A bot can extract invoice data, verify it against purchase orders and receipts, update accounting systems, and even flag exceptions for human review—all without manual intervention for standard cases.

Human resources is another area seeing significant RPA implementation. Bots can streamline employee onboarding by automatically creating accounts across multiple systems, processing paperwork, and ensuring compliance requirements are met. They can also assist with payroll processing, benefits administration, and routine employee queries.

Customer service operations benefit from RPA through faster processing of standard requests. Bots can retrieve customer information across multiple systems, update records, process simple requests, and route complex issues to the appropriate human agents with all relevant information already gathered.

While RPA offers clear advantages in efficiency and accuracy, its impact on employment remains a complex issue. Some routine positions may be eliminated as tasks are automated, but new roles are also emerging to design, implement, and oversee RPA systems. Many organizations are retraining employees to handle more complex, judgment-intensive work while delegating routine tasks to bots.

The most successful RPA implementations tend to focus on augmenting human capabilities rather than replacing workers entirely. By handling repetitive, time-consuming tasks, bots free up employees to focus on activities that require creativity, emotional intelligence, and complex decision-making—areas where humans still maintain a significant advantage over automation.

As RPA technology continues to evolve, particularly through integration with artificial intelligence, its capabilities will extend beyond simple rule-based tasks to more complex processes requiring judgment and adaptation. This progression will likely accelerate the transformation of work across many industries in the coming years.
                    """,
                    read_time=7,
                    featured=False,
                    featured_image="/static/images/posts/rpa.svg",
                    category_id=2,  # Automation
                    author_id=1,  # Jane Doe
                ),
                Post(
                    title="The Rise of Quantum Computing in Tech Industry",
                    slug="quantum-computing-tech-industry",
                    excerpt="Recent breakthroughs in quantum computing and how major tech companies are investing in this technology.",
                    content="""
Quantum computing represents one of the most promising and revolutionary technologies on the horizon, with the potential to solve complex problems that remain intractable for even the most powerful classical computers. Major tech companies and research institutions are investing heavily in this field, recognizing its transformative potential across numerous industries.

Unlike classical computers that use bits (0s and 1s) as their fundamental units of information, quantum computers utilize quantum bits or "qubits." Through the quantum mechanical properties of superposition and entanglement, qubits can exist in multiple states simultaneously and exhibit correlations that allow quantum computers to process vast amounts of information in ways impossible for classical systems.

IBM has been at the forefront of quantum computing development, making quantum processors available through cloud services and steadily increasing the number and quality of qubits in their systems. Their roadmap aims to build a 1,000+ qubit quantum computer by 2023, a significant milestone toward practical quantum advantage.

Google made headlines in 2019 by claiming "quantum supremacy" when their 53-qubit Sycamore processor reportedly solved a specific problem in 200 seconds that would take the world's most powerful supercomputer thousands of years. While this achievement has been debated, it represented a significant step forward in demonstrating quantum computing's potential.

Microsoft is pursuing a different approach with topological qubits, which could potentially be more stable and less prone to errors than other qubit technologies. Though more experimental, this approach could eventually lead to more reliable quantum computing systems requiring less extensive error correction.

Amazon has entered the quantum race through Amazon Braket, a cloud service that provides access to various quantum hardware from providers like D-Wave, IonQ, and Rigetti. This marketplace approach allows researchers and businesses to experiment with different quantum technologies without major hardware investments.

Beyond the tech giants, countries are making substantial national investments in quantum computing research. China, the United States, Germany, and others have launched multi-billion dollar initiatives to advance quantum technologies, recognizing their strategic importance for future economic and national security applications.

The potential applications of mature quantum computing span numerous fields. In pharmaceuticals, quantum computers could model molecular interactions to accelerate drug discovery. Financial services could use them for portfolio optimization and risk analysis. Materials science could benefit from quantum simulations to develop new materials with specific properties. Cryptography will likely be transformed, with quantum computers potentially breaking current encryption methods while also enabling new quantum-secure protocols.

While fully fault-tolerant, general-purpose quantum computers remain years away, specialized quantum systems are already beginning to tackle specific problems. The rapid pace of advancement in the field suggests that quantum computing will increasingly impact various industries over the coming decade, potentially solving problems that have long resisted classical approaches.
                    """,
                    read_time=9,
                    featured=False,
                    featured_image="/static/images/posts/quantum.svg",
                    category_id=3,  # Tech News
                    author_id=2,  # John Smith
                )
            ]
            
            db.session.add_all(posts)
            db.session.commit()
            
            # Add topics to posts
            posts[0].topics.extend([topics[0], topics[1]])  # Cryptocurrency, Blockchain
            posts[1].topics.extend([topics[2], topics[3]])  # Smart Home, AI
            posts[2].topics.extend([topics[5], topics[3]])  # Apple, AI
            posts[3].topics.extend([topics[1], topics[6]])  # Blockchain, Google
            posts[4].topics.extend([topics[3], topics[4]])  # AI, Machine Learning
            posts[5].topics.extend([topics[3], topics[7]])  # AI, Microsoft
            posts[6].topics.extend([topics[2], topics[7]])  # AI, Microsoft
            
            db.session.commit()

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404



# STEP 1: Route for Access Token Creation
@app.route('/SiddarthaDas_trading/create_token')
def create_access_token():
    """Route to create access token"""
    return render_template('create_token.html')

@app.route('/SiddarthaDas_trading/generate_token', methods=['POST'])
def generate_access_token():
    """Generate access token using Fyers API"""
    try:
        from fyers_apiv3 import fyersModel
        
        # Create session model
        session = fyersModel.SessionModel(
            client_id=CLIENT_ID,
            secret_key=SECRET_KEY,
            redirect_uri=REDIRECT_URI,
            response_type="code"
        )
        
        # Generate auth code URL
        auth_url = session.generate_authcode()
        
        return jsonify({
            'status': 'success',
            'auth_url': auth_url,
            'message': 'Please complete authentication and provide the callback URL'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error generating auth URL: {str(e)}'
        }), 500

@app.route('/SiddarthaDas_trading/save_token', methods=['POST'])
def save_access_token():
    """Save access token from callback URL"""
    try:
        data = request.get_json()
        callback_url = data.get('callback_url')
        
        if not callback_url:
            return jsonify({
                'status': 'error',
                'message': 'Callback URL is required'
            }), 400
        
        # Extract auth code from URL
        if 'auth_code=' in callback_url:
            auth_code = callback_url.split('auth_code=')[1].split('&')[0]
        else:
            return jsonify({
                'status': 'error',
                'message': 'Auth code not found in callback URL'
            }), 400
        
        # Generate access token
        from fyers_apiv3 import fyersModel
        
        session = fyersModel.SessionModel(
            client_id=CLIENT_ID,
            secret_key=SECRET_KEY,
            redirect_uri=REDIRECT_URI,
            response_type="code",
            grant_type="authorization_code"
        )
        
        session.set_token(auth_code)
        response = session.generate_token()
        
        if 'access_token' in response:
            access_token = response['access_token']
            
            # Save to state file
            state = read_trading_state()
            state['access_token'] = access_token
            state['token_date'] = datetime.now().isoformat()
            write_trading_state(state)
            
            # Also save to daily file (as your script expects)
            today = dt.now('Asia/Kolkata').date()
            with open(f'/home/siddartha1192/blogging/access-{today}.txt', 'w') as f:
                f.write(access_token)
            
            log_trading_event("Access token generated successfully")
            
            return jsonify({
                'status': 'success',
                'message': 'Access token saved successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to generate token: {response}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error saving token: {str(e)}'
        }), 500




@app.route('/SiddarthaDas_trading/create_stop_signal', methods=['POST'])
def create_stop_signal():
    """Create stop signal file for graceful shutdown"""
    try:
        stop_file = '/home/siddartha1192/blogging/trading_stop_signal.txt'
        
        with open(stop_file, 'w') as f:
            f.write('STOP_REQUESTED')
        
        log_trading_event("Stop signal file created")
        
        return jsonify({
            'status': 'success',
            'message': 'Stop signal file created successfully'
        })
        
    except Exception as e:
        log_trading_event(f"Error creating stop signal: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error creating stop signal: {str(e)}'
        }), 500

@app.route('/SiddarthaDas_trading/api/processes')
def get_running_processes():
    """Get all running UpdatedLatest.py processes"""
    try:
        running_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('UpdatedLatest.py' in arg for arg in cmdline):
                    running_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(cmdline) if cmdline else 'N/A'
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return jsonify({
            'status': 'success',
            'processes': running_processes,
            'count': len(running_processes)
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking processes: {str(e)}',
            'processes': []
        }), 500


# STEP 2: Route to Start Trading Script
@app.route('/SiddarthaDas_trading/start_script', methods=['POST'])
def start_trading_script():
    """Start the trading script"""
    try:
        state = read_trading_state()
        
        # Check if access token exists
        if not state.get('access_token'):
            return jsonify({
                'status': 'error',
                'message': 'Access token not found. Please create token first.'
            }), 400
        
        # Check if already running
        runningStatus = str(state.get('trading_active'))
        print("The trading script running status is:", runningStatus)
        if runningStatus != 'false':
            return jsonify({
                'status': 'warning',
                'message': 'Trading script is already running, testing status: ' + runningStatus
            })
        
        # Start the trading script as subprocess
        script_path = '/home/siddartha1192/blogging/UpdatedLatest.py'  # Your trading script
        if not os.path.exists(script_path):
            return jsonify({
                'status': 'error',
                'message': f'Trading script {script_path} not found'
            }), 404
        
        # Start process
        script_path = '/home/siddartha1192/blogging/UpdatedLatest.py'
        cmd = f'"{sys.executable}" "{script_path}" > /home/siddartha1192/blogging/trading_log.txt 2>&1'
        process = subprocess.Popen(cmd, shell=True, cwd=os.path.dirname(script_path))
        
        # Update state
        state['trading_active'] = True
        state['process_id'] = process.pid
        state['last_started'] = datetime.now().isoformat()
        state['script_status'] = 'running'
        write_trading_state(state)
        
        log_trading_event(f"Trading script started with PID: {process.pid}")
        
        return jsonify({
            'status': 'success',
            'message': f'Trading script started successfully with PID: {process.pid}'
        })
        
    except Exception as e:
        log_trading_event(f"Error starting script: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error starting trading script: {str(e)}'
        }), 500

# STEP 3: Dashboard Route
@app.route('/SiddarthaDas_trading/dashboard')
def trading_dashboard():
    """Main trading dashboard"""
    state = read_trading_state()
    
    # Read recent logs
    recent_logs = []
    try:
        if os.path.exists(TRADING_LOG_FILE):
            with open(TRADING_LOG_FILE, 'r') as f:
                lines = f.readlines()
                recent_logs = lines[-20:]  # Last 20 lines
                recent_logs.reverse()  # Most recent first
    except:
        recent_logs = ['No logs available']
    
    # Check if process is actually running
    if state.get('process_id'):
        try:
            process = psutil.Process(state['process_id'])
            if process.is_running():
                state['script_status'] = 'running'
            else:
                state['script_status'] = 'stopped'
                state['trading_active'] = 'false'
        except:
            state['script_status'] = 'stopped'
            state['trading_active'] = 'false'
    
    # Get CSV files for reports
    csv_files = []
    for file in os.listdir('.'):
        if file.startswith('trades_nifty_supertrend_option_selling_') and file.endswith('.csv'):
            csv_files.append(file)
    
    return render_template('trading_dashboard.html', 
                         state=state, 
                         recent_logs=recent_logs,
                         csv_files=csv_files)

# STEP 4: Route to Stop Trading Script
@app.route('/SiddarthaDas_trading/stop_script', methods=['POST'])
def stop_trading_script():
    """Stop the trading script with multiple methods"""
    try:
        state = read_trading_state()
        
        if not state.get('trading_active') or not state.get('process_id'):
            return jsonify({
                'status': 'warning',
                'message': 'No trading script is currently running'
            })
        
        process_id = state['process_id']
        
        # Method 1: Create stop signal file
        stop_file = '/home/siddartha1192/blogging/trading_stop_signal.txt'
        try:
            with open(stop_file, 'w') as f:
                f.write('STOP')
            log_trading_event("Stop signal file created")
        except Exception as e:
            log_trading_event(f"Failed to create stop file: {e}")
        
        # Method 2: Try graceful termination
        try:
            process = psutil.Process(process_id)
            if process.is_running():
                # Send SIGTERM first (graceful shutdown)
                process.terminate()
                log_trading_event(f"SIGTERM sent to process {process_id}")
                
                # Wait up to 15 seconds for graceful shutdown
                try:
                    process.wait(timeout=15)
                    log_trading_event("Process terminated gracefully")
                except psutil.TimeoutExpired:
                    log_trading_event("Graceful shutdown timeout, forcing kill")
                    # Force kill if timeout
                    process.kill()
                    try:
                        process.wait(timeout=5)
                        log_trading_event("Process force killed")
                    except psutil.TimeoutExpired:
                        log_trading_event("Process still running after force kill")
                
            else:
                log_trading_event("Process was not running")
                
        except psutil.NoSuchProcess:
            log_trading_event("Process no longer exists")
        except Exception as e:
            log_trading_event(f"Error during process termination: {e}")
        
        # Method 3: Try to kill by name if PID method fails
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('UpdatedLatest.py' in arg for arg in cmdline):
                        proc.kill()
                        log_trading_event(f"Killed UpdatedLatest.py process with PID {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            log_trading_event(f"Error killing by name: {e}")
        
        # Method 4: Update state regardless
        state['trading_active'] = 'false'
        state['process_id'] = None
        state['last_stopped'] = datetime.now().isoformat()
        state['script_status'] = 'stopped'
        write_trading_state(state)
        
        log_trading_event("Trading script stop attempted with multiple methods")
        
        # Wait a moment and check if any UpdatedLatest.py processes are still running
        time.sleep(2)
        still_running = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('UpdatedLatest.py' in arg for arg in cmdline):
                        still_running.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass
        
        if still_running:
            return jsonify({
                'status': 'warning',
                'message': f'Stop signal sent, but processes may still be running: {still_running}. Check again in a few moments.'
            })
        else:
            return jsonify({
                'status': 'success',
                'message': 'Trading script stopped successfully'
            })
            
    except Exception as e:
        log_trading_event(f"Error stopping script: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error stopping trading script: {str(e)}'
        }), 500
    

@app.route('/SiddarthaDas_trading/force_stop', methods=['POST'])
def force_stop_all():
    """Force stop all UpdatedLatest.py processes"""
    try:
        killed_processes = []
        
        # Create stop signal file
        stop_file = '/home/siddartha1192/blogging/trading_stop_signal.txt'
        with open(stop_file, 'w') as f:
            f.write('FORCE_STOP')
        
        # Kill all processes running UpdatedLatest.py
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('UpdatedLatest.py' in arg for arg in cmdline):
                    proc.kill()
                    killed_processes.append(proc.info['pid'])
                    log_trading_event(f"Force killed process {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Update state
        state = read_trading_state()
        state['trading_active'] = 'false'
        state['process_id'] = None
        state['last_stopped'] = datetime.now().isoformat()
        state['script_status'] = 'force_stopped'
        write_trading_state(state)
        
        if killed_processes:
            message = f'Force stopped {len(killed_processes)} processes: {killed_processes}'
        else:
            message = 'No UpdatedLatest.py processes found running'
        
        log_trading_event(message)
        
        return jsonify({
            'status': 'success',
            'message': message
        })
        
    except Exception as e:
        log_trading_event(f"Error in force stop: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error in force stop: {str(e)}'
        }), 500



@app.route('/SiddarthaDas_trading/generate_report', methods=['POST'])
def generate_trading_report():
    """Generate trading report from CSV"""
    try:
        data = request.get_json()
        csv_file = data.get('csv_file')
        
        if not csv_file:
            return jsonify({
                'status': 'error',
                'message': 'CSV file name is required'
            }), 400
        
        if not os.path.exists(csv_file):
            return jsonify({
                'status': 'error',
                'message': f'CSV file {csv_file} not found'
            }), 404
        
        # Import and use your HTML report generator
        import sys
        sys.path.append('.')  # Add current directory to path
        
        from Html_Play import NiftyOptionsAnalyzer
        
        # Create analyzer and generate report
        analyzer = NiftyOptionsAnalyzer(lot_size=75)
        output_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # Process the file
        result = analyzer.process_file(csv_file, output_file)
        
        if result:
            log_trading_event(f"Report generated: {output_file}")
            return jsonify({
                'status': 'success',
                'message': f'Report generated successfully: {output_file}',
                'report_file': output_file
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate report'
            }), 500
            
    except Exception as e:
        log_trading_event(f"Error generating report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating report: {str(e)}'
        }), 500

@app.route('/SiddarthaDas_trading/view_report/<filename>')
def view_trading_report(filename):
    """View generated HTML report"""
    try:
        if not filename.endswith('.html'):
            filename += '.html'
        
        if not os.path.exists(filename):
            flash(f'Report file {filename} not found', 'error')
            return redirect(url_for('trading_dashboard'))
        
        # Read and serve the HTML file
        with open(filename, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return html_content
        
    except Exception as e:
        flash(f'Error viewing report: {str(e)}', 'error')
        return redirect(url_for('trading_dashboard'))

# API Routes for AJAX calls
@app.route('/SiddarthaDas_trading/api/status')
def get_trading_status():
    """Get current trading status via API with improved process checking"""
    state = read_trading_state()
    
    # Check if any UpdatedLatest.py processes are running
    running_processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and any('UpdatedLatest.py' in arg for arg in cmdline):
                    running_processes.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except:
        pass
    
    # Update state based on actual running processes
    if running_processes:
        if len(running_processes) == 1:
            state['process_id'] = running_processes[0]
        state['trading_active'] = True
        state['script_status'] = 'running'
        state['process_running'] = True
        state['actual_running_pids'] = running_processes
    else:
        state['trading_active'] = 'false'
        state['process_id'] = None
        state['script_status'] = 'stopped'
        state['process_running'] = 'false'
        state['actual_running_pids'] = []
    
    # Save updated state
    write_trading_state(state)
    
    return jsonify(state)

@app.route('/SiddarthaDas_trading/api/logs')
def get_recent_logs():
    """Get recent trading logs via API"""
    try:
        logs = []

        # Read from main trading log file   
        if os.path.exists(TRADING_LOG_FILE):
            with open(TRADING_LOG_FILE, 'r') as f:
                lines = f.readlines()
                logs.extend(lines[-10:][::-1])  # Last 10 lines, most recent first

        # Prepare today's date format
        today_str = datetime.now().strftime('%Y-%m-%d')

        # Search for matching additional log file in current directory
        current_dir = '/home/siddartha1192/blogging/'
        for fname in os.listdir(current_dir):
            if fname.startswith("nifty_supertrend_option_selling") and today_str in fname:
                file_path = os.path.join(current_dir, fname)
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    logs.extend(lines[-20:][::-1])
                break  # Stop after the first match

        return jsonify({
            'status': 'success',
            'logs': logs
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# Helper route to check token validity
@app.route('/SiddarthaDas_trading/check_token')
def check_token_validity():
    """Check if current access token is valid"""
    try:
        state = read_trading_state()
        
        if not state.get('access_token'):
            return jsonify({
                'status': 'error',
                'message': 'No access token found'
            })
        
        # Try to initialize Fyers with current token
        from fyers_apiv3 import fyersModel
        
        fyers = fyersModel.FyersModel(
            client_id=CLIENT_ID,
            is_async=False,
            token=state['access_token'],
            log_path=None
        )
        
        # Try to get profile to check if token is valid
        profile = fyers.get_profile()
        
        if profile.get('s') == 'ok':
            return jsonify({
                'status': 'success',
                'message': 'Access token is valid',
                'token_date': state.get('token_date')
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Access token is invalid or expired'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error checking token: {str(e)}'
        })




# Create placeholder images for avatars and posts
def create_placeholder_images():
    avatar_dir = os.path.join(app.static_folder, 'images/avatars')
    posts_dir = os.path.join(app.static_folder, 'images/posts')
    
    # Create directories if they don't exist
    os.makedirs(avatar_dir, exist_ok=True)
    os.makedirs(posts_dir, exist_ok=True)
    
    # Create avatar placeholders
    avatar1_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="100" fill="#4CAF50"/>
  <circle cx="100" cy="80" r="40" fill="#FFFFFF"/>
  <path d="M100 130 Q 65 130 50 170 Q 75 190 100 190 Q 125 190 150 170 Q 135 130 100 130" fill="#FFFFFF"/>
</svg>"""
    
    avatar2_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="100" fill="#2196F3"/>
  <circle cx="100" cy="80" r="40" fill="#FFFFFF"/>
  <path d="M100 130 Q 65 130 50 170 Q 75 190 100 190 Q 125 190 150 170 Q 135 130 100 130" fill="#FFFFFF"/>
</svg>"""
    
    if not os.path.exists(os.path.join(avatar_dir, 'avatar-1.svg')):
        with open(os.path.join(avatar_dir, 'avatar-1.svg'), 'w') as f:
            f.write(avatar1_svg)
    
    if not os.path.exists(os.path.join(avatar_dir, 'avatar-2.svg')):
        with open(os.path.join(avatar_dir, 'avatar-2.svg'), 'w') as f:
            f.write(avatar2_svg)
    
    # Create post image placeholders
    crypto_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="#FF9800"/>
  <circle cx="400" cy="200" r="100" fill="#FFFFFF"/>
  <text x="400" y="220" font-family="Arial" font-size="70" font-weight="bold" text-anchor="middle" fill="#FF9800">₿</text>
  <text x="400" y="350" font-family="Arial" font-size="36" text-anchor="middle" fill="#FFFFFF">Cryptocurrency & Banking</text>
</svg>"""
    
    smarthome_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="#4CAF50"/>
  <path d="M400 100 L250 200 L250 350 L550 350 L550 200 Z" fill="#FFFFFF"/>
  <rect x="370" y="270" width="60" height="80" fill="#4CAF50"/>
  <circle cx="330" cy="250" r="25" fill="#4CAF50"/>
  <circle cx="470" cy="250" r="25" fill="#4CAF50"/>
  <text x="400" y="350" font-family="Arial" font-size="36" text-anchor="middle" fill="#FFFFFF">Smart Home Automation</text>
</svg>"""
    
    apple_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="#000000"/>
  <rect x="300" y="100" width="200" height="200" fill="#FFFFFF" rx="20" ry="20"/>
  <text x="400" y="230" font-family="Arial" font-size="100" text-anchor="middle" fill="#000000">M3</text>
  <text x="400" y="350" font-family="Arial" font-size="36" text-anchor="middle" fill="#FFFFFF">Apple Silicon</text>
</svg>"""
    
    blockchain_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="#3F51B5"/>
  <rect x="150" y="150" width="100" height="100" fill="#FFFFFF" rx="10" ry="10"/>
  <rect x="350" y="150" width="100" height="100" fill="#FFFFFF" rx="10" ry="10"/>
  <rect x="550" y="150" width="100" height="100" fill="#FFFFFF" rx="10" ry="10"/>
  <line x1="250" y1="200" x2="350" y2="200" stroke="#FFFFFF" stroke-width="10"/>
  <line x1="450" y1="200" x2="550" y2="200" stroke="#FFFFFF" stroke-width="10"/>
  <text x="400" y="350" font-family="Arial" font-size="36" text-anchor="middle" fill="#FFFFFF">Blockchain Technology</text>
</svg>"""
    
    rpa_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="#2196F3"/>
  <rect x="300" y="150" width="200" height="150" fill="#FFFFFF"/>
  <circle cx="400" cy="125" r="50" fill="#FFFFFF"/>
  <line x1="350" y1="200" x2="450" y2="200" stroke="#2196F3" stroke-width="10"/>
  <line x1="350" y1="230" x2="450" y2="230" stroke="#2196F3" stroke-width="10"/>
  <line x1="350" y1="260" x2="450" y2="260" stroke="#2196F3" stroke-width="10"/>
  <text x="400" y="350" font-family="Arial" font-size="36" text-anchor="middle" fill="#FFFFFF">Robotic Process Automation</text>
</svg>"""
    
    quantum_svg = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="800" height="400" fill="#9C27B0"/>
  <circle cx="400" cy="200" r="100" fill="none" stroke="#FFFFFF" stroke-width="5"/>
  <circle cx="400" cy="200" r="20" fill="#FFFFFF"/>
  <ellipse cx="400" cy="200" rx="150" ry="50" fill="none" stroke="#FFFFFF" stroke-width="5" transform="rotate(30 400 200)"/>
  <ellipse cx="400" cy="200" rx="150" ry="50" fill="none" stroke="#FFFFFF" stroke-width="5" transform="rotate(150 400 200)"/>
  <text x="400" y="350" font-family="Arial" font-size="36" text-anchor="middle" fill="#FFFFFF">Quantum Computing</text>
</svg>"""
    
    post_images = {
        'crypto-banking.svg': crypto_svg,
        'smart-home.svg': smarthome_svg,
        'apple-chip.svg': apple_svg,
        'blockchain.svg': blockchain_svg,
        'rpa.svg': rpa_svg,
        'quantum.svg': quantum_svg
    }
    
    for img_name, svg_content in post_images.items():
        if not os.path.exists(os.path.join(posts_dir, img_name)):
            with open(os.path.join(posts_dir, img_name), 'w') as f:
                f.write(svg_content)

# Initialize the database and create placeholder images
init_db()
create_placeholder_images()

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
