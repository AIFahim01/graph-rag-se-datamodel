"""
Generate dummy PDF files for testing

Creates realistic sample PDFs for each project with domain-specific content.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from pathlib import Path
from datetime import datetime


class DummyPDFGenerator:
    """Generate dummy PDF documents for testing"""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor='darkblue',
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor='darkblue',
            spaceAfter=12
        ))

    def create_pdf(self, filename: str, title: str, content_sections: list):
        """Create a PDF with given title and content sections"""
        filepath = self.output_dir / filename
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []

        # Title
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3 * inch))

        # Metadata
        date_str = datetime.now().strftime("%B %d, %Y")
        story.append(Paragraph(f"<b>Date:</b> {date_str}", self.styles['Normal']))
        story.append(Paragraph(f"<b>Document Type:</b> {filename.replace('_', ' ').replace('.pdf', '').title()}", self.styles['Normal']))
        story.append(Spacer(1, 0.5 * inch))

        # Content sections
        for section in content_sections:
            story.append(Paragraph(section['title'], self.styles['SectionHeader']))
            story.append(Spacer(1, 0.2 * inch))

            for paragraph in section['content']:
                story.append(Paragraph(paragraph, self.styles['BodyText']))
                story.append(Spacer(1, 0.15 * inch))

            story.append(Spacer(1, 0.3 * inch))

        doc.build(story)
        print(f"✓ Generated: {filepath}")


def generate_project_001_pdfs(generator: DummyPDFGenerator):
    """Generate PDFs for Project 001: Alpha ERP System"""
    print("\nGenerating PDFs for Project 001: Alpha ERP System")

    # Technical Offer
    tech_offer_content = [
        {
            'title': '1. Executive Summary',
            'content': [
                'We propose a comprehensive ERP solution for ABC Corporation to streamline manufacturing operations, improve inventory management, and enhance supply chain visibility.',
                'Our solution leverages SAP S/4HANA with custom modules for production planning and real-time analytics.',
                'The implementation will be phased over 12 months with minimal disruption to ongoing operations.'
            ]
        },
        {
            'title': '2. Technical Architecture',
            'content': [
                'The proposed architecture consists of three tiers: presentation layer (SAP Fiori), application layer (SAP S/4HANA), and data layer (HANA database).',
                'Integration with existing systems will be achieved through REST APIs and SAP PI/PO middleware.',
                'High availability will be ensured through active-active clustering across two data centers.',
                'Security measures include role-based access control, data encryption at rest and in transit, and regular security audits.'
            ]
        },
        {
            'title': '3. Modules and Functionality',
            'content': [
                'Material Management (MM): Purchase order management, inventory tracking, vendor management, and procurement workflows.',
                'Production Planning (PP): Master production scheduling, capacity planning, shop floor control, and quality management.',
                'Sales and Distribution (SD): Order management, pricing, delivery scheduling, and billing integration.',
                'Finance and Controlling (FICO): General ledger, accounts payable/receivable, asset accounting, and cost center accounting.',
                'Warehouse Management (WM): Bin management, picking strategies, goods receipt/issue, and inventory optimization.'
            ]
        },
        {
            'title': '4. Implementation Methodology',
            'content': [
                'We follow SAP Activate methodology with iterative development and continuous stakeholder engagement.',
                'Phase 1 (Months 1-3): Requirements gathering, system design, and infrastructure setup.',
                'Phase 2 (Months 4-7): Core module configuration, custom development, and integration.',
                'Phase 3 (Months 8-10): User acceptance testing, data migration, and training.',
                'Phase 4 (Months 11-12): Go-live preparation, hypercare support, and knowledge transfer.'
            ]
        }
    ]
    generator.create_pdf('technical_offer.pdf', 'ERP Implementation - Technical Proposal', tech_offer_content)

    # Commercial Offer
    comm_offer_content = [
        {
            'title': '1. Pricing Structure',
            'content': [
                'Software Licenses: SAP S/4HANA Enterprise Edition - $450,000 (one-time)',
                'Implementation Services: 2,400 hours @ $185/hour - $444,000',
                'Infrastructure Setup: Cloud hosting setup and configuration - $75,000',
                'Training and Change Management: Comprehensive user training program - $85,000',
                'Annual Support and Maintenance: 22% of license cost - $99,000/year (starting Year 2)'
            ]
        },
        {
            'title': '2. Payment Terms',
            'content': [
                '30% upon contract signing and project kickoff',
                '40% upon successful completion of Phase 2 (core modules configured)',
                '20% upon user acceptance testing completion',
                '10% upon go-live and system acceptance',
                'Payment terms: Net 30 days from invoice date'
            ]
        },
        {
            'title': '3. Deliverables',
            'content': [
                'Fully configured SAP S/4HANA system with all specified modules',
                'Custom integrations with existing legacy systems',
                'Comprehensive documentation including technical design, user manuals, and operational procedures',
                'Training materials and recorded training sessions',
                '90 days of post-go-live hypercare support',
                '12 months warranty on all implementation work'
            ]
        },
        {
            'title': '4. Terms and Conditions',
            'content': [
                'Proposal validity: 60 days from date of submission',
                'Project duration: 12 months from contract signing',
                'Travel and expenses will be billed at cost',
                'Change requests will be managed through formal change control process',
                'Client responsibilities include timely access to systems, data, and subject matter experts'
            ]
        }
    ]
    generator.create_pdf('commercial_offer.pdf', 'ERP Implementation - Commercial Proposal', comm_offer_content)

    # RFQ Response
    rfq_content = [
        {
            'title': '1. Company Overview',
            'content': [
                'Our company has 15+ years of experience implementing ERP solutions for manufacturing enterprises.',
                'We have successfully completed 200+ SAP implementations across various industries.',
                'Our team consists of 50+ certified SAP consultants with deep manufacturing domain expertise.',
                'We maintain SAP Gold Partner status and have received multiple implementation excellence awards.'
            ]
        },
        {
            'title': '2. Understanding of Requirements',
            'content': [
                'ABC Corporation requires an integrated ERP system to replace legacy systems and spreadsheets.',
                'Key pain points include: lack of real-time inventory visibility, manual production planning, disconnected financial reporting.',
                'Expected benefits: 30% reduction in inventory carrying costs, 25% improvement in on-time delivery, real-time financial visibility.',
                'Critical success factors: minimal business disruption, comprehensive user training, data accuracy post-migration.'
            ]
        },
        {
            'title': '3. Proposed Solution',
            'content': [
                'SAP S/4HANA Cloud or On-Premise based on client preference and data sovereignty requirements.',
                'Pre-configured industry templates for discrete manufacturing to accelerate implementation.',
                'Mobile-enabled interfaces for shop floor workers and warehouse staff.',
                'Advanced analytics with embedded AI for demand forecasting and predictive maintenance.',
                'Seamless integration with existing MES (Manufacturing Execution System) and quality management tools.'
            ]
        },
        {
            'title': '4. Team Composition',
            'content': [
                'Project Manager: PMP certified with 10+ years SAP implementation experience',
                'Solution Architect: SAP Certified with expertise in manufacturing industry',
                'Module Consultants: Specialists in MM, PP, SD, FICO, and WM modules (5-8 years experience each)',
                'Technical Consultants: ABAP developers, integration specialists, and database administrators',
                'Change Management Lead: Organizational change expert with manufacturing focus'
            ]
        }
    ]
    generator.create_pdf('rfq_response.pdf', 'Response to RFQ - ERP System', rfq_content)

    # Technical Specifications
    specs_content = [
        {
            'title': '1. System Requirements',
            'content': [
                'Application Server: SUSE Linux Enterprise Server 15, 32 vCPU, 256GB RAM, 2TB SSD storage',
                'Database Server: SAP HANA 2.0 SPS06, 64 vCPU, 512GB RAM, 5TB SSD storage (hot), 10TB HDD (cold)',
                'Web Dispatcher: 8 vCPU, 16GB RAM, 500GB storage for load balancing',
                'Backup Infrastructure: Daily incremental, weekly full backups with 30-day retention',
                'Network: 10 Gbps internal network, 1 Gbps internet connectivity, redundant firewalls'
            ]
        },
        {
            'title': '2. Integration Specifications',
            'content': [
                'Legacy ERP: Batch data extraction via SFTP, nightly synchronization of master data',
                'MES System: Real-time production data exchange via OPC UA protocol',
                'Quality Management: API-based integration for inspection results and non-conformance reports',
                'BI/Analytics: Direct HANA connectivity for reporting and analytics tools',
                'Email System: SMTP integration for notifications and workflow approvals'
            ]
        },
        {
            'title': '3. Security Requirements',
            'content': [
                'Authentication: Single Sign-On (SSO) with Active Directory integration',
                'Authorization: Role-based access control (RBAC) with segregation of duties enforcement',
                'Data Protection: AES-256 encryption for data at rest, TLS 1.3 for data in transit',
                'Audit Logging: Comprehensive audit trails for all transactions and configuration changes',
                'Compliance: SOC 2 Type II, ISO 27001, and GDPR compliance requirements'
            ]
        },
        {
            'title': '4. Performance Requirements',
            'content': [
                'System Availability: 99.9% uptime during business hours (6 AM - 10 PM)',
                'Response Time: <2 seconds for 95% of transactions, <5 seconds for complex reports',
                'Concurrent Users: Support for 500 concurrent users with peak load of 750 users',
                'Batch Processing: Nightly batch jobs must complete within 4-hour window (2 AM - 6 AM)',
                'Data Volume: Initial data load of 5 million material records, 2 million customer records, 10 years of transaction history'
            ]
        }
    ]
    generator.create_pdf('technical_specifications.pdf', 'ERP System - Technical Specifications', specs_content)


def generate_project_002_pdfs(generator: DummyPDFGenerator):
    """Generate PDFs for Project 002: Beta Cloud Migration"""
    print("\nGenerating PDFs for Project 002: Beta Cloud Migration")

    # Technical Offer
    tech_offer_content = [
        {
            'title': '1. Migration Strategy',
            'content': [
                'We propose a phased lift-and-shift migration followed by cloud-native optimization for XYZ Tech Solutions.',
                'The migration will leverage AWS as the primary cloud provider with multi-region deployment for high availability.',
                'Our approach minimizes downtime through parallel run strategy and automated rollback capabilities.',
                'Post-migration optimization will focus on containerization, auto-scaling, and serverless architecture where applicable.'
            ]
        },
        {
            'title': '2. Cloud Architecture',
            'content': [
                'Multi-tier architecture with separate VPCs for production, staging, and development environments.',
                'Application layer: Kubernetes clusters (EKS) for containerized microservices with auto-scaling.',
                'Data layer: Amazon RDS for relational databases, DynamoDB for NoSQL, S3 for object storage.',
                'Networking: AWS Transit Gateway for inter-VPC connectivity, Direct Connect for on-premise integration.',
                'Security: AWS WAF, Shield for DDoS protection, GuardDuty for threat detection, CloudTrail for audit logging.'
            ]
        },
        {
            'title': '3. Migration Phases',
            'content': [
                'Phase 1: Assessment and Planning (Weeks 1-4) - Infrastructure inventory, dependency mapping, migration wave planning.',
                'Phase 2: Foundation Setup (Weeks 5-8) - Landing zone creation, network configuration, security baseline.',
                'Phase 3: Application Migration (Weeks 9-20) - Database migration, application replatforming, testing and validation.',
                'Phase 4: Optimization (Weeks 21-24) - Performance tuning, cost optimization, automation implementation.',
                'Phase 5: Cutover and Stabilization (Weeks 25-28) - Final migration, DNS cutover, hypercare support.'
            ]
        }
    ]
    generator.create_pdf('cloud_migration_proposal.pdf', 'Cloud Migration - Technical Proposal', tech_offer_content)

    # Commercial Offer
    comm_offer_content = [
        {
            'title': '1. Professional Services',
            'content': [
                'Migration Planning and Assessment: $95,000',
                'Infrastructure Setup and Configuration: $145,000',
                'Application Migration Services: $285,000',
                'Database Migration and Optimization: $125,000',
                'Testing and Validation: $75,000',
                'Training and Knowledge Transfer: $45,000',
                'Total Professional Services: $770,000'
            ]
        },
        {
            'title': '2. Cloud Infrastructure Costs (Monthly Estimates)',
            'content': [
                'Compute (EC2 instances): $15,000/month',
                'Managed Kubernetes (EKS): $8,000/month',
                'Database Services (RDS, DynamoDB): $12,000/month',
                'Storage (S3, EBS): $5,000/month',
                'Networking and Data Transfer: $4,000/month',
                'Security and Monitoring: $3,000/month',
                'Estimated Monthly Infrastructure Cost: $47,000',
                'Note: Actual costs may vary based on usage patterns and will be optimized post-migration.'
            ]
        },
        {
            'title': '3. Managed Services (Optional)',
            'content': [
                '24/7 Infrastructure Management: $25,000/month',
                'Security Operations Center (SOC): $15,000/month',
                'Backup and Disaster Recovery Management: $8,000/month',
                'Performance Monitoring and Optimization: $12,000/month',
                'Cost Optimization Services: $5,000/month'
            ]
        }
    ]
    generator.create_pdf('cloud_migration_commercial.pdf', 'Cloud Migration - Commercial Proposal', comm_offer_content)

    # Migration Specifications
    specs_content = [
        {
            'title': '1. Current Infrastructure Inventory',
            'content': [
                'Physical Servers: 45 servers (mix of application, database, and web servers)',
                'Virtual Machines: 120 VMs running on VMware vSphere 7.0',
                'Databases: 15 SQL Server databases, 8 Oracle databases, 5 PostgreSQL databases',
                'Storage: 85TB total storage across SAN and NAS systems',
                'Applications: 35 business applications including custom-developed and COTS'
            ]
        },
        {
            'title': '2. Target Cloud Architecture',
            'content': [
                'Regions: Primary in us-east-1, DR in us-west-2 for geographic redundancy',
                'Compute: Mix of EC2 instances (m5, c5, r5 families) and EKS clusters',
                'Networking: 3-tier VPC architecture with public, private, and database subnets',
                'Load Balancing: Application Load Balancers for HTTP/HTTPS, Network Load Balancers for TCP',
                'Auto-scaling: Configured based on CPU, memory, and custom application metrics'
            ]
        },
        {
            'title': '3. Migration Methodology',
            'content': [
                'Discovery: Automated discovery using AWS Application Discovery Service and CloudEndure',
                'Assessment: 7Rs framework (Retain, Rehost, Replatform, Refactor, Repurchase, Retire, Relocate)',
                'Data Migration: AWS Database Migration Service for databases, AWS DataSync for file storage',
                'Application Migration: CloudEndure for server migration, manual replatforming for cloud-native',
                'Testing: Comprehensive testing including functional, performance, security, and disaster recovery tests'
            ]
        }
    ]
    generator.create_pdf('migration_specifications.pdf', 'Cloud Migration - Technical Specifications', specs_content)


def generate_project_003_pdfs(generator: DummyPDFGenerator):
    """Generate PDFs for Project 003: Gamma Data Analytics Platform"""
    print("\nGenerating PDFs for Project 003: Gamma Data Analytics Platform")

    # Technical Offer
    tech_offer_content = [
        {
            'title': '1. Platform Overview',
            'content': [
                'We propose a real-time data analytics platform for Data Insights Inc to process financial market data at scale.',
                'The platform leverages Apache Kafka for data ingestion, Apache Spark for processing, and Elasticsearch for search and analytics.',
                'Machine learning models built with TensorFlow will provide predictive analytics and anomaly detection.',
                'Interactive dashboards powered by custom visualization framework will deliver actionable insights to traders and analysts.'
            ]
        },
        {
            'title': '2. Technical Architecture',
            'content': [
                'Data Ingestion Layer: Kafka clusters processing 500,000+ events/second from multiple market data feeds',
                'Stream Processing: Spark Structured Streaming for real-time transformations and aggregations',
                'Batch Processing: Spark batch jobs for historical analysis and model training',
                'Storage Layer: Data Lake (S3/HDFS) for raw data, Elasticsearch for indexed data, PostgreSQL for metadata',
                'ML Pipeline: Kubeflow for model training, serving, and monitoring with A/B testing capabilities',
                'API Layer: FastAPI for RESTful services, WebSocket for real-time data streaming to clients'
            ]
        },
        {
            'title': '3. Key Features',
            'content': [
                'Real-time market data processing with sub-100ms latency',
                'Anomaly detection using unsupervised learning algorithms',
                'Predictive models for price forecasting and trend analysis',
                'Natural language processing for news sentiment analysis',
                'Customizable alerts and notifications based on configurable rules',
                'Historical data replay for backtesting trading strategies',
                'Role-based access control with audit logging for compliance'
            ]
        }
    ]
    generator.create_pdf('analytics_platform_proposal.pdf', 'Data Analytics Platform - Technical Proposal', tech_offer_content)

    # RFQ Response
    rfq_content = [
        {
            'title': '1. Understanding of Requirements',
            'content': [
                'Data Insights Inc requires a scalable platform to ingest, process, and analyze real-time financial market data.',
                'Key requirements: Handle 500K+ events/second, <100ms latency, support for 200+ concurrent users.',
                'Integration with existing: Bloomberg terminals, internal risk systems, trading platforms.',
                'Compliance: Must meet financial regulations including data retention, audit trails, and access controls.',
                'Scalability: Platform must scale to 2M events/second within 2 years.'
            ]
        },
        {
            'title': '2. Proposed Solution',
            'content': [
                'Cloud-native architecture deployed on Kubernetes for elasticity and resilience.',
                'Microservices-based design for independent scaling and deployment of components.',
                'Event-driven architecture using Kafka for loose coupling and replay capability.',
                'Multi-layer caching strategy for frequently accessed data to reduce latency.',
                'Machine learning models deployed as containerized services with automatic scaling.',
                'Comprehensive monitoring and observability using Prometheus, Grafana, and ELK stack.'
            ]
        },
        {
            'title': '3. Implementation Approach',
            'content': [
                'Agile development with 2-week sprints and continuous integration/deployment.',
                'MVP delivery in 12 weeks with core ingestion, processing, and visualization capabilities.',
                'Iterative addition of ML models and advanced analytics features.',
                'Parallel infrastructure setup and application development to accelerate time-to-market.',
                'Continuous performance testing and optimization throughout development.',
                'User acceptance testing with actual market data in staging environment.'
            ]
        }
    ]
    generator.create_pdf('analytics_rfq_response.pdf', 'Response to RFQ - Data Analytics Platform', rfq_content)

    # System Specifications
    specs_content = [
        {
            'title': '1. Performance Requirements',
            'content': [
                'Data Ingestion: 500,000 events/second sustained, 1,000,000 events/second peak',
                'Processing Latency: <100ms end-to-end for real-time stream processing',
                'Query Response: <1 second for simple queries, <5 seconds for complex aggregations',
                'Dashboard Load Time: <2 seconds for initial load, <500ms for updates',
                'Concurrent Users: Support 200+ concurrent analysts and traders',
                'Data Retention: 7 years hot storage, infinite cold storage for compliance'
            ]
        },
        {
            'title': '2. Data Sources',
            'content': [
                'Market Data Feeds: Bloomberg, Reuters, internal proprietary feeds',
                'Trading Data: Order executions, positions, P&L from trading systems',
                'News and Social Media: Financial news APIs, Twitter streams for sentiment analysis',
                'Reference Data: Security master, exchange calendars, corporate actions',
                'Alternative Data: Satellite imagery, web scraping data, IoT sensor data'
            ]
        },
        {
            'title': '3. Technology Stack',
            'content': [
                'Data Ingestion: Apache Kafka 3.x, Kafka Connect for source connectors',
                'Stream Processing: Apache Spark 3.x Structured Streaming, Apache Flink (backup option)',
                'Batch Processing: Apache Spark with Delta Lake for ACID transactions',
                'Storage: AWS S3/Azure Blob for data lake, Elasticsearch 8.x for search',
                'Machine Learning: TensorFlow 2.x, PyTorch, Scikit-learn, MLflow for experiment tracking',
                'Orchestration: Apache Airflow for batch jobs, Kubernetes for container orchestration',
                'Visualization: React-based custom dashboards, D3.js for interactive charts'
            ]
        },
        {
            'title': '4. Security and Compliance',
            'content': [
                'Authentication: Multi-factor authentication with SSO integration',
                'Authorization: Fine-grained RBAC with attribute-based access control for sensitive data',
                'Encryption: TLS 1.3 for data in transit, AES-256 for data at rest',
                'Audit Logging: Comprehensive logging of all data access and system changes',
                'Compliance: SOC 2 Type II, SOX compliance for financial data handling',
                'Data Masking: PII and sensitive data masking for non-production environments'
            ]
        }
    ]
    generator.create_pdf('analytics_specifications.pdf', 'Data Analytics Platform - System Specifications', specs_content)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate dummy PDF files for testing")
    parser.add_argument(
        '--datasets-dir',
        type=str,
        default='./datasets',
        help='Path to datasets directory (default: ./datasets)'
    )

    args = parser.parse_args()

    datasets_dir = Path(args.datasets_dir)
    projects_dir = datasets_dir / 'projects'

    if not projects_dir.exists():
        print(f"❌ Projects directory not found: {projects_dir}")
        return

    print("=" * 80)
    print("GENERATING DUMMY PDF FILES")
    print("=" * 80)

    # Generate PDFs for each project
    try:
        # Project 001
        project_001 = projects_dir / 'project_001'
        if project_001.exists():
            gen1 = DummyPDFGenerator(project_001)
            generate_project_001_pdfs(gen1)

        # Project 002
        project_002 = projects_dir / 'project_002'
        if project_002.exists():
            gen2 = DummyPDFGenerator(project_002)
            generate_project_002_pdfs(gen2)

        # Project 003
        project_003 = projects_dir / 'project_003'
        if project_003.exists():
            gen3 = DummyPDFGenerator(project_003)
            generate_project_003_pdfs(gen3)

        print("\n" + "=" * 80)
        print("✓ All PDFs generated successfully!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Run: python scripts/dataset_stats.py")
        print("2. Run: python scripts/process_project.py --all")
        print()

    except Exception as e:
        print(f"\n❌ Error generating PDFs: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
