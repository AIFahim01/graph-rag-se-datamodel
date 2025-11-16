export async function GET(request: Request) {
  const url = new URL(request.url)
  const query = url.searchParams.get("q")

  if (!query) {
    return Response.json({ error: "Query parameter is required" }, { status: 400 })
  }

  try {
    // Call Python FastAPI backend for real Neo4j vector search
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const response = await fetch(`${backendUrl}/api/search?q=${encodeURIComponent(query)}`)

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }

    const data = await response.json()
    return Response.json(data)

  } catch (error) {
    console.error('Error calling backend API:', error)

    // Fallback to mock data if backend unavailable
    const mockResults = [
    {
      id: "1",
      title: "Understanding Machine Learning Fundamentals",
      description: "A comprehensive guide to machine learning concepts, algorithms, and best practices for beginners.",
      category: "Machine Learning",
      relevance: 0.95,
      content: `Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without explicit programming.

## Key Concepts

### Supervised Learning
Supervised learning uses labeled training data where both inputs and desired outputs are provided. Common applications include:
- Classification (predicting categories)
- Regression (predicting continuous values)

### Unsupervised Learning
Unsupervised learning discovers patterns in unlabeled data:
- Clustering (grouping similar items)
- Dimensionality reduction (simplifying data)

### Reinforcement Learning
The model learns by interacting with an environment and receiving rewards or penalties.

## Best Practices

1. Data Preprocessing: Clean and normalize your data
2. Feature Engineering: Select relevant features for your model
3. Model Selection: Choose appropriate algorithms for your problem
4. Hyperparameter Tuning: Optimize model performance
5. Validation: Use cross-validation and test sets
6. Monitoring: Track model performance in production`,
      tags: ["machine-learning", "ai", "algorithms", "tutorial", "beginner-friendly"],
      metadata: {
        author: "Dr. Jane Smith",
        views: 15420,
        rating: 4.8,
        difficulty: "Beginner",
        duration: "2 hours",
      },
      source: "ML Academy",
      createdAt: "2024-01-15",
    },
    {
      id: "2",
      title: "Advanced Neural Networks and Deep Learning",
      description:
        "Explore deep learning architectures, CNNs, RNNs, and transformer models with practical implementations.",
      category: "Deep Learning",
      relevance: 0.87,
      content: `Deep learning is a subset of machine learning based on artificial neural networks with multiple layers.

## Neural Network Architectures

### Convolutional Neural Networks (CNN)
Specialized for processing grid-like data such as images:
- Convolutional layers for feature extraction
- Pooling layers for dimensionality reduction
- Fully connected layers for classification

### Recurrent Neural Networks (RNN)
Designed for sequential data processing:
- LSTM (Long Short-Term Memory) cells
- GRU (Gated Recurrent Unit)
- Bidirectional processing

### Transformer Architecture
Revolutionary architecture for sequence-to-sequence tasks:
- Multi-head attention mechanism
- Positional encoding
- Feed-forward networks

## Implementation Tips

- Use frameworks like TensorFlow or PyTorch
- Start with pre-trained models (transfer learning)
- Use GPU acceleration for training
- Implement proper regularization techniques
- Monitor training with visualization tools`,
      tags: ["deep-learning", "neural-networks", "ai", "advanced", "implementation"],
      metadata: {
        author: "Prof. John Doe",
        views: 8932,
        rating: 4.7,
        difficulty: "Advanced",
        duration: "4 hours",
      },
      source: "Deep Learning Institute",
      createdAt: "2024-02-20",
    },
    {
      id: "3",
      title: "Natural Language Processing with Transformers",
      description: "Learn NLP techniques using state-of-the-art transformer models like BERT and GPT.",
      category: "NLP",
      relevance: 0.82,
      content: `Natural Language Processing (NLP) enables computers to understand and generate human language.

## Core NLP Tasks

### Text Classification
Categorizing text into predefined categories:
- Sentiment analysis
- Topic classification
- Spam detection

### Named Entity Recognition (NER)
Identifying and classifying named entities in text:
- Person names
- Locations
- Organizations

### Sequence-to-Sequence Models
Translating between sequences:
- Machine translation
- Summarization
- Question answering

## Transformer Models

### BERT (Bidirectional Encoder Representations)
Excellent for understanding context:
- Pre-trained on large corpora
- Fine-tune for downstream tasks
- State-of-the-art performance

### GPT (Generative Pre-trained Transformer)
Powerful for text generation:
- Autoregressive approach
- Few-shot learning capabilities
- Creative content generation`,
      tags: ["nlp", "transformers", "bert", "gpt", "language-models"],
      metadata: {
        author: "Sarah Johnson",
        views: 6721,
        rating: 4.6,
        difficulty: "Intermediate",
        duration: "3 hours",
      },
      source: "NLP Hub",
      createdAt: "2024-03-10",
    },
    {
      id: "4",
      title: "Computer Vision: From Theory to Implementation",
      description:
        "Master computer vision techniques including image classification, object detection, and segmentation.",
      category: "Computer Vision",
      relevance: 0.78,
      content: `Computer vision enables machines to interpret and understand visual information from the world.

## Core Computer Vision Tasks

### Image Classification
Assigning labels to entire images:
- Binary classification
- Multi-class classification
- Multi-label classification

### Object Detection
Locating and classifying objects within images:
- YOLO (You Only Look Once)
- R-CNN family
- SSD (Single Shot Detector)

### Image Segmentation
Pixel-level classification:
- Semantic segmentation
- Instance segmentation
- Panoptic segmentation

## Popular Architectures

### ResNet
Deep residual networks with skip connections:
- Solves vanishing gradient problem
- Enables very deep networks
- Transfer learning backbone

### U-Net
Encoder-decoder architecture for segmentation:
- Skip connections between encoder and decoder
- Excellent for medical imaging
- Efficient with limited data`,
      tags: ["computer-vision", "image-processing", "object-detection", "cnn"],
      metadata: {
        author: "Michael Chen",
        views: 5234,
        rating: 4.5,
        difficulty: "Intermediate",
        duration: "3.5 hours",
      },
      source: "Vision Lab",
      createdAt: "2024-02-28",
    },
    {
      id: "5",
      title: "Reinforcement Learning: Building Intelligent Agents",
      description: "Learn how to build autonomous agents using reinforcement learning and Q-learning algorithms.",
      category: "Reinforcement Learning",
      relevance: 0.71,
      content: `Reinforcement Learning (RL) trains agents to make decisions by interacting with an environment.

## Core Concepts

### Markov Decision Process (MDP)
Mathematical framework for RL:
- States: Current situation
- Actions: Available choices
- Rewards: Feedback signal
- Policy: Strategy for action selection

### Value Functions
Estimating expected returns:
- State-value function V(s)
- Action-value function Q(s,a)
- Bellman equations

## Key Algorithms

### Q-Learning
Model-free algorithm for learning optimal policies:
- Off-policy learning
- Temporal difference updates
- Exploration vs exploitation

### Deep Q-Networks (DQN)
Combining Q-learning with deep neural networks:
- Experience replay
- Target networks
- Handles high-dimensional state spaces

### Policy Gradient Methods
Directly optimizing the policy:
- REINFORCE algorithm
- Actor-Critic methods
- Proximal Policy Optimization (PPO)`,
      tags: ["reinforcement-learning", "q-learning", "agents", "dqn", "policy-gradient"],
      metadata: {
        author: "Emily Rodriguez",
        views: 4123,
        rating: 4.4,
        difficulty: "Advanced",
        duration: "4.5 hours",
      },
      source: "RL Research Lab",
      createdAt: "2024-03-05",
    },
    {
      id: "6",
      title: "Data Science with Python: A Complete Guide",
      description: "Master data analysis, visualization, and statistical modeling using Python libraries like Pandas and NumPy.",
      category: "Data Science",
      relevance: 0.68,
      content: `Data Science combines statistics, programming, and domain expertise to extract insights from data.

## Essential Python Libraries

### Pandas
Data manipulation and analysis:
- DataFrames for structured data
- Data cleaning and preprocessing
- Time series analysis

### NumPy
Numerical computing foundation:
- Multi-dimensional arrays
- Mathematical functions
- Linear algebra operations

### Matplotlib & Seaborn
Data visualization:
- Statistical plots
- Customizable charts
- Publication-quality figures`,
      tags: ["data-science", "python", "pandas", "numpy", "visualization"],
      metadata: {
        author: "David Lee",
        views: 7845,
        rating: 4.7,
        difficulty: "Beginner",
        duration: "3 hours",
      },
      source: "Data Science Hub",
      createdAt: "2024-01-20",
    },
    {
      id: "7",
      title: "Cloud Computing Fundamentals: AWS, Azure, and GCP",
      description: "Learn cloud infrastructure, deployment strategies, and best practices across major cloud platforms.",
      category: "Cloud Computing",
      relevance: 0.65,
      content: `Cloud computing provides on-demand access to computing resources over the internet.

## Major Cloud Providers

### Amazon Web Services (AWS)
Leading cloud platform:
- EC2 for compute
- S3 for storage
- Lambda for serverless

### Microsoft Azure
Enterprise-focused cloud:
- Virtual Machines
- Azure Functions
- Cosmos DB

### Google Cloud Platform (GCP)
Data and AI focused:
- Compute Engine
- BigQuery
- Cloud AI Platform`,
      tags: ["cloud-computing", "aws", "azure", "gcp", "devops"],
      metadata: {
        author: "Rachel Green",
        views: 5632,
        rating: 4.5,
        difficulty: "Intermediate",
        duration: "4 hours",
      },
      source: "Cloud Academy",
      createdAt: "2024-02-15",
    },
    {
      id: "8",
      title: "Web Development with React and Next.js",
      description: "Build modern, performant web applications using React and the Next.js framework.",
      category: "Web Development",
      relevance: 0.62,
      content: `Modern web development with React and Next.js enables building fast, SEO-friendly applications.

## React Fundamentals

### Components
Building blocks of React apps:
- Functional components
- Props and state
- Hooks (useState, useEffect)

### Next.js Features

#### Server-Side Rendering
Improved performance and SEO:
- Static generation
- Server components
- API routes

#### Routing
File-based routing system:
- Dynamic routes
- Nested layouts
- Middleware`,
      tags: ["web-development", "react", "nextjs", "javascript", "frontend"],
      metadata: {
        author: "Alex Turner",
        views: 9234,
        rating: 4.8,
        difficulty: "Intermediate",
        duration: "5 hours",
      },
      source: "Web Dev Academy",
      createdAt: "2024-03-01",
    },
    {
      id: "9",
      title: "Cybersecurity Essentials: Protecting Your Systems",
      description: "Learn security fundamentals, threat detection, and best practices for protecting digital assets.",
      category: "Cybersecurity",
      relevance: 0.59,
      content: `Cybersecurity protects systems, networks, and data from digital attacks.

## Core Security Concepts

### Authentication & Authorization
Identity management:
- Multi-factor authentication
- OAuth and JWT
- Role-based access control

### Encryption
Data protection:
- Symmetric encryption
- Public key cryptography
- SSL/TLS protocols

### Threat Detection
Identifying attacks:
- Intrusion detection systems
- Security monitoring
- Incident response`,
      tags: ["cybersecurity", "security", "encryption", "authentication", "networking"],
      metadata: {
        author: "Marcus Johnson",
        views: 6123,
        rating: 4.6,
        difficulty: "Intermediate",
        duration: "3.5 hours",
      },
      source: "Security Institute",
      createdAt: "2024-02-10",
    },
    {
      id: "10",
      title: "Database Design and SQL Mastery",
      description: "Master relational database design, SQL queries, and optimization techniques.",
      category: "Database",
      relevance: 0.56,
      content: `Database design and SQL are fundamental skills for managing structured data.

## Database Design Principles

### Normalization
Organizing data efficiently:
- First normal form (1NF)
- Second normal form (2NF)
- Third normal form (3NF)

### SQL Queries

#### Basic Operations
CRUD operations:
- SELECT statements
- JOIN operations
- Aggregation functions

#### Advanced Techniques
Performance optimization:
- Indexing strategies
- Query optimization
- Transaction management`,
      tags: ["database", "sql", "postgresql", "mysql", "data-modeling"],
      metadata: {
        author: "Lisa Wang",
        views: 8456,
        rating: 4.7,
        difficulty: "Beginner",
        duration: "4 hours",
      },
      source: "Database Academy",
      createdAt: "2024-01-25",
    },
    {
      id: "11",
      title: "Mobile App Development with React Native",
      description: "Build cross-platform mobile applications for iOS and Android using React Native.",
      category: "Mobile Development",
      relevance: 0.53,
      content: `React Native enables building native mobile apps using JavaScript and React.

## React Native Fundamentals

### Core Components
Building mobile UIs:
- View and Text
- ScrollView and FlatList
- TouchableOpacity

### Navigation
App navigation patterns:
- Stack navigation
- Tab navigation
- Drawer navigation

### Native Features
Accessing device capabilities:
- Camera and photos
- Geolocation
- Push notifications`,
      tags: ["mobile-development", "react-native", "ios", "android", "javascript"],
      metadata: {
        author: "Chris Martinez",
        views: 7234,
        rating: 4.6,
        difficulty: "Intermediate",
        duration: "5 hours",
      },
      source: "Mobile Dev Hub",
      createdAt: "2024-02-25",
    },
    {
      id: "12",
      title: "DevOps and CI/CD Pipeline Automation",
      description: "Implement continuous integration and deployment pipelines for efficient software delivery.",
      category: "DevOps",
      relevance: 0.50,
      content: `DevOps practices streamline software development and deployment processes.

## CI/CD Fundamentals

### Continuous Integration
Automated testing and building:
- Version control integration
- Automated testing
- Build automation

### Continuous Deployment
Automated release process:
- Deployment pipelines
- Environment management
- Rollback strategies

### Tools and Technologies

#### Popular CI/CD Tools
- Jenkins
- GitHub Actions
- GitLab CI
- CircleCI`,
      tags: ["devops", "ci-cd", "automation", "jenkins", "docker"],
      metadata: {
        author: "Tom Anderson",
        views: 5987,
        rating: 4.5,
        difficulty: "Advanced",
        duration: "4.5 hours",
      },
      source: "DevOps Institute",
      createdAt: "2024-03-08",
    },
    {
      id: "13",
      title: "Blockchain and Cryptocurrency Fundamentals",
      description: "Understand blockchain technology, cryptocurrencies, and decentralized applications.",
      category: "Blockchain",
      relevance: 0.47,
      content: `Blockchain is a distributed ledger technology enabling secure, transparent transactions.

## Core Concepts

### Blockchain Structure
Distributed ledger:
- Blocks and chains
- Consensus mechanisms
- Cryptographic hashing

### Smart Contracts
Self-executing contracts:
- Ethereum platform
- Solidity programming
- DApp development

### Cryptocurrencies
Digital currencies:
- Bitcoin fundamentals
- Altcoins and tokens
- Wallet management`,
      tags: ["blockchain", "cryptocurrency", "ethereum", "bitcoin", "web3"],
      metadata: {
        author: "Nina Patel",
        views: 4567,
        rating: 4.4,
        difficulty: "Intermediate",
        duration: "3 hours",
      },
      source: "Blockchain Academy",
      createdAt: "2024-02-18",
    },
    {
      id: "14",
      title: "Artificial Intelligence Ethics and Governance",
      description: "Explore ethical considerations, bias mitigation, and responsible AI development practices.",
      category: "AI Ethics",
      relevance: 0.44,
      content: `AI ethics addresses the moral implications and societal impact of artificial intelligence.

## Key Ethical Considerations

### Bias and Fairness
Ensuring equitable AI:
- Data bias detection
- Algorithmic fairness
- Inclusive design

### Privacy and Security
Protecting user data:
- Data minimization
- Differential privacy
- Secure AI systems

### Transparency and Accountability
Responsible AI development:
- Explainable AI
- Audit trails
- Governance frameworks`,
      tags: ["ai-ethics", "responsible-ai", "bias", "privacy", "governance"],
      metadata: {
        author: "Dr. James Wilson",
        views: 3892,
        rating: 4.7,
        difficulty: "Advanced",
        duration: "2.5 hours",
      },
      source: "Ethics Institute",
      createdAt: "2024-03-12",
    },
    {
      id: "15",
      title: "Internet of Things (IoT) Development",
      description: "Build connected devices and IoT applications using sensors, microcontrollers, and cloud platforms.",
      category: "IoT",
      relevance: 0.41,
      content: `IoT connects physical devices to the internet, enabling data collection and remote control.

## IoT Components

### Hardware
Physical devices:
- Microcontrollers (Arduino, ESP32)
- Sensors and actuators
- Communication modules

### Connectivity
Network protocols:
- WiFi and Bluetooth
- MQTT protocol
- LoRaWAN

### Cloud Integration
Data processing:
- AWS IoT Core
- Azure IoT Hub
- Google Cloud IoT`,
      tags: ["iot", "embedded-systems", "arduino", "sensors", "mqtt"],
      metadata: {
        author: "Kevin Brown",
        views: 5123,
        rating: 4.5,
        difficulty: "Intermediate",
        duration: "4 hours",
      },
      source: "IoT Academy",
      createdAt: "2024-01-30",
    },
  ]

  // Filter results based on query (simple keyword matching for demo)
  const filteredResults = mockResults.filter(
    (result) =>
      result.title.toLowerCase().includes(query.toLowerCase()) ||
      result.description.toLowerCase().includes(query.toLowerCase()) ||
      result.category.toLowerCase().includes(query.toLowerCase()),
  )

  // Sort by relevance
  filteredResults.sort((a, b) => b.relevance - a.relevance)

  return Response.json({
    results: filteredResults.length > 0 ? filteredResults : mockResults.slice(0, 3),
    query,
    count: filteredResults.length,
  })
  }
}
