import { Candidate, Requirement, AppReportStats, TimelineEvent, RecruiterNote } from '../types';

export const INITIAL_REQUIREMENTS: Requirement[] = [
  {
    id: 'req-1',
    title: 'Senior PMO Executive / Delivery Lead',
    description: 'Looking for an experienced PMO Executive with strong MIS reporting, stakeholder coordination, and project tracking expertise.',
    requiredSkills: ['PMO', 'Stakeholder Management', 'Power BI', 'SQL', 'MIS Reporting'],
    preferredSkills: ['Jira', 'Excel', 'Resource Management', 'Python'],
    minExperienceYears: 2,
    maxExperienceYears: 6,
    location: 'Mumbai / Hybrid',
    noticePeriod: '30 Days',
    employmentType: 'Full-time',
    education: 'Bachelor degree in Technology or Business',
    activeCandidateMatchesCount: 4,
    createdAt: '2026-07-20',
  },
  {
    id: 'req-2',
    title: 'Sr. Java Backend Developer (Banking Domain)',
    description: 'Core Java, Spring Boot, Microservices specialist needed for digital banking solutions.',
    requiredSkills: ['Java', 'Spring Boot', 'Microservices', 'PostgreSQL', 'REST API'],
    preferredSkills: ['Kafka', 'Docker', 'AWS', 'Redis'],
    minExperienceYears: 5,
    maxExperienceYears: 9,
    location: 'Bangalore / Remote',
    noticePeriod: 'Immediate to 30 Days',
    employmentType: 'Full-time',
    education: 'B.Tech / B.E. Computer Science',
    activeCandidateMatchesCount: 3,
    createdAt: '2026-07-22',
  },
  {
    id: 'req-3',
    title: 'Data Analyst & BI Specialist',
    description: 'Data analytics expert to build executive dashboards and perform complex SQL queries.',
    requiredSkills: ['Power BI', 'SQL', 'Python', 'Advanced Excel'],
    preferredSkills: ['Tableau', 'ETL Pipeline', 'Snowflake'],
    minExperienceYears: 3,
    maxExperienceYears: 7,
    location: 'Pune / Remote',
    employmentType: 'Full-time',
    activeCandidateMatchesCount: 5,
    createdAt: '2026-07-24',
  }
];

export const INITIAL_CANDIDATES: Candidate[] = [
  {
    id: 'cand-1',
    name: 'Aarav Mehta',
    designation: 'PMO Executive',
    email: 'aarav.mehta@example.com',
    phone: '+91 98200 12345',
    linkedinUrl: 'https://linkedin.com/in/aarav-mehta-pmo',
    githubUrl: null,
    portfolioUrl: null,
    location: 'Mumbai, India',
    noticePeriod: '30 Days',
    expectedSalary: '₹14,00,000 / yr',
    experienceMonths: 29,
    experienceYears: 2.4,
    experienceDisplay: '2 Years 5 Months',
    currentCompany: 'ABC Technologies',
    latestCompany: 'ABC Technologies',
    professionalSummary: 'Detail-oriented PMO Executive with 2.4+ years of experience steering IT projects, designing Power BI MIS dashboards, and facilitating cross-functional stakeholder alignments for major enterprise clients in retail and finance.',
    topSkills: ['PMO', 'Power BI', 'SQL', 'Stakeholder Management', 'Advanced Excel', 'MIS Reporting'],
    categorizedSkills: [
      {
        category: 'Project/Management Skills',
        skills: ['PMO', 'Stakeholder Management', 'Resource Management', 'Risk Mitigation', 'Agile Governance']
      },
      {
        category: 'Technical & Analytics',
        skills: ['Power BI', 'SQL', 'Excel', 'Python (Basic)']
      },
      {
        category: 'Tools',
        skills: ['Jira', 'Confluence', 'Advanced Excel', 'MS Project']
      }
    ],
    experiences: [
      {
        id: 'exp-1',
        company: 'ABC Technologies',
        designation: 'PMO Executive',
        startDate: 'Feb 2024',
        endDate: 'Present',
        isCurrent: true,
        durationDisplay: '2 Years 5 Months',
        responsibilities: [
          'Managed end-to-end project tracking and sprint governance across 4 client accounts.',
          'Prepared daily/weekly MIS reports and automated Power BI KPI dashboards for C-suite leaders.',
          'Coordinated with cross-functional technical teams, mitigating project delays by 18%.'
        ],
        clients: ['Honeywell', 'HSBC', 'IKEA']
      },
      {
        id: 'exp-2',
        company: 'NexGen Digital Solutions',
        designation: 'Associate Project Coordinator',
        startDate: 'Mar 2022',
        endDate: 'Jan 2024',
        isCurrent: false,
        durationDisplay: '1 Year 11 Months',
        responsibilities: [
          'Assisted Project Managers in sprint planning, resource allocation, and budget tracking.',
          'Maintained project documentation and facilitated daily standups.'
        ]
      }
    ],
    education: [
      {
        id: 'edu-1',
        institution: 'University of Mumbai',
        degree: 'Bachelor of Science in Information Technology',
        startDate: '2018',
        endDate: '2021'
      }
    ],
    certifications: ['Certified Associate in Project Management (CAPM)', 'Power BI Data Analyst Associate'],
    matchScore: 88,
    matchBreakdown: {
      overall: 88,
      mandatorySkills: 95,
      preferredSkills: 80,
      experience: 90,
      education: 85,
      roleMatch: 90,
      matchingSkills: ['PMO', 'Power BI', 'SQL', 'Stakeholder Management', 'MIS Reporting', 'Jira', 'Excel'],
      missingMandatorySkills: [],
      missingPreferredSkills: ['Python'],
      strengths: [
        'Direct experience managing PMO operations for enterprise tier-1 clients (Honeywell, HSBC).',
        'Strong hands-on mastery in both analytical reporting (Power BI, SQL) and managerial coordination.'
      ],
      gaps: [
        'Python experience is limited compared to full data engineering profiles.'
      ],
      explanation: 'Exceeds mandatory skill criteria for PMO Executive role. Employer ABC Technologies client assignments directly align with requirement needs.'
    },
    aiInsights: {
      strengths: [
        'Demonstrated employer vs client governance (ABC Technologies with Honeywell/HSBC).',
        'Hands-on reporting automation via Power BI and SQL.',
        'Structured sprint tracking and MIS presentation skills.'
      ],
      experienceSummary: '2.4+ years focused on PMO operations, MIS reporting, and multi-client coordination.',
      coreSkills: ['PMO', 'Power BI', 'SQL', 'Stakeholder Management', 'Jira'],
      potentialRoles: ['PMO Lead', 'Delivery Coordinator', 'Senior Project Analyst'],
      careerProgression: 'Consistent advancement from Associate Coordinator to PMO Executive with increasing portfolio authority.'
    },
    contactHistory: [
      {
        date: '2026-07-25',
        type: 'Phone Call',
        note: 'Recruiter called candidate regarding PMO opening. Candidate expressed high interest.'
      }
    ],
    uploadedAt: '2026-07-25 14:30'
  },
  {
    id: 'cand-2',
    name: 'Priya Sharma',
    designation: 'Sr. Java Backend Engineer',
    email: 'priya.sharma@devhub.net',
    phone: '+91 99870 54321',
    linkedinUrl: 'https://linkedin.com/in/priya-sharma-java',
    githubUrl: 'https://github.com/priyasharma-backend',
    portfolioUrl: null,
    location: 'Bangalore, India',
    noticePeriod: null, // Null to reflect Anti-Hallucination rule
    expectedSalary: null, // Null to reflect Anti-Hallucination rule
    experienceMonths: 74,
    experienceYears: 6.2,
    experienceDisplay: '6 Years 2 Months',
    currentCompany: 'FinTech Innovations Pvt Ltd',
    latestCompany: 'FinTech Innovations Pvt Ltd',
    professionalSummary: 'Senior Java Backend Engineer with 6+ years specializing in high-throughput microservices architecture, Spring Boot, PostgreSQL, and Kafka event streams in banking and payment domains.',
    topSkills: ['Java', 'Spring Boot', 'Microservices', 'PostgreSQL', 'REST API', 'Kafka', 'Docker'],
    categorizedSkills: [
      {
        category: 'Backend Languages & Frameworks',
        skills: ['Java 17', 'Spring Boot', 'Spring Cloud', 'Hibernate', 'REST API']
      },
      {
        category: 'Databases & Messaging',
        skills: ['PostgreSQL', 'Redis', 'Kafka', 'MySQL']
      },
      {
        category: 'DevOps & Tools',
        skills: ['Docker', 'Kubernetes (Basic)', 'Git', 'Jenkins', 'Maven']
      }
    ],
    experiences: [
      {
        id: 'exp-201',
        company: 'FinTech Innovations Pvt Ltd',
        designation: 'Senior Backend Engineer',
        startDate: 'Oct 2022',
        endDate: 'Present',
        isCurrent: true,
        durationDisplay: '3 Years 10 Months',
        responsibilities: [
          'Architected core payment gateway integration processing over 2M transactions daily.',
          'Migrated monolithic core billing application to Spring Boot microservices with 99.99% uptime.',
          'Optimized SQL query response time on PostgreSQL by 42%.'
        ],
        clients: ['HDFC Bank', 'Axis Securities']
      },
      {
        id: 'exp-202',
        company: 'Rakuten India',
        designation: 'Software Development Engineer II',
        startDate: 'May 2020',
        endDate: 'Sep 2022',
        isCurrent: false,
        durationDisplay: '2 Years 5 Months',
        responsibilities: [
          'Developed microservices for e-commerce checkout and recommendation pipelines.'
        ]
      }
    ],
    education: [
      {
        id: 'edu-201',
        institution: 'National Institute of Technology, Surathkal',
        degree: 'B.Tech in Computer Science & Engineering',
        startDate: '2016',
        endDate: '2020'
      }
    ],
    certifications: ['AWS Certified Developer - Associate', 'Oracle Certified Professional Java SE 11'],
    matchScore: 94,
    matchBreakdown: {
      overall: 94,
      mandatorySkills: 100,
      preferredSkills: 90,
      experience: 95,
      education: 90,
      roleMatch: 95,
      matchingSkills: ['Java', 'Spring Boot', 'Microservices', 'PostgreSQL', 'REST API', 'Kafka', 'Docker'],
      missingMandatorySkills: [],
      missingPreferredSkills: ['AWS'],
      strengths: [
        'Perfect match on mandatory skills with 6+ years hands-on Java microservices experience.',
        'Verified Banking/FinTech domain background with client work for HDFC Bank.'
      ],
      gaps: [],
      explanation: 'Top tier match for Banking Java role. High experience depth with Kafka and microservices migration.'
    },
    aiInsights: {
      strengths: [
        'Solid computer science fundamentals from NIT Surathkal.',
        'Demonstrated experience handling high-volume transaction processing (2M daily calls).',
        'Proven expertise with PostgreSQL performance tuning.'
      ],
      experienceSummary: '6.2 years in backend systems development across FinTech and e-commerce platforms.',
      coreSkills: ['Java', 'Spring Boot', 'Microservices', 'Kafka', 'PostgreSQL'],
      potentialRoles: ['Sr. Java Developer', 'Backend Architect', 'Technical Lead'],
      careerProgression: 'Rapid career growth from Software Engineer to Senior Backend Engineer at FinTech Innovations.'
    },
    contactHistory: [],
    uploadedAt: '2026-07-26 10:15'
  },
  {
    id: 'cand-3',
    name: 'Vikramaditya Roy',
    designation: 'Senior Data & BI Specialist',
    email: 'vikram.roy@analytics.org',
    phone: '+91 97111 88990',
    linkedinUrl: 'https://linkedin.com/in/vikram-roy-data',
    githubUrl: null,
    portfolioUrl: null,
    location: 'Pune, India',
    noticePeriod: ' Immediate ',
    expectedSalary: '₹18,00,000 / yr',
    experienceMonths: 60,
    experienceYears: 5.0,
    experienceDisplay: '5 Years 0 Months',
    currentCompany: 'DataPoint Analytics',
    latestCompany: 'DataPoint Analytics',
    professionalSummary: 'Data Analyst & BI Specialist with 5 years experience creating executive dashboards, designing complex ETL queries in SQL, and automating Python data pipelines for global logistics clients.',
    topSkills: ['Power BI', 'SQL', 'Python', 'Advanced Excel', 'Tableau', 'Snowflake', 'ETL Pipeline'],
    categorizedSkills: [
      {
        category: 'Data Analytics & Visualization',
        skills: ['Power BI', 'Tableau', 'Excel DAX', 'Advanced Excel']
      },
      {
        category: 'Database & Warehousing',
        skills: ['PostgreSQL', 'Snowflake', 'MySQL', 'BigQuery']
      },
      {
        category: 'Programming & Pipelines',
        skills: ['Python', 'Pandas', 'NumPy', 'ETL Pipelines']
      }
    ],
    experiences: [
      {
        id: 'exp-301',
        company: 'DataPoint Analytics',
        designation: 'Lead Data Analyst',
        startDate: 'Jul 2021',
        endDate: 'Present',
        isCurrent: true,
        durationDisplay: '5 Years 0 Months',
        responsibilities: [
          'Led a team of 3 data analysts building executive operational dashboards for Fortune 500 logistics clients.',
          'Built Python automated scripts reducing data preparation time by 65%.'
        ],
        clients: ['FedEx Express', 'Maersk Line']
      }
    ],
    education: [
      {
        id: 'edu-301',
        institution: 'Pune University',
        degree: 'B.Sc in Statistics & Computer Science'
      }
    ],
    certifications: ['Microsoft Certified: Power BI Data Analyst Associate'],
    matchScore: 91,
    matchBreakdown: {
      overall: 91,
      mandatorySkills: 100,
      preferredSkills: 85,
      experience: 90,
      education: 85,
      roleMatch: 92,
      matchingSkills: ['Power BI', 'SQL', 'Python', 'Advanced Excel', 'Tableau', 'Snowflake'],
      missingMandatorySkills: [],
      missingPreferredSkills: [],
      strengths: [
        'Strong mastery of Power BI, DAX, and automated Python ETL pipelines.',
        'Immediate availability.'
      ],
      gaps: [],
      explanation: 'Strong candidate for BI Specialist requirement. Includes both Tableau and Snowflake skills.'
    },
    aiInsights: {
      strengths: ['Dual mastery in Power BI and Tableau visualization frameworks', 'Strong mathematical/statistical background from Pune University'],
      experienceSummary: '5 years of quantitative analytics and dashboard design.',
      coreSkills: ['Power BI', 'SQL', 'Python', 'ETL', 'Snowflake'],
      potentialRoles: ['Senior BI Analyst', 'Data Analytics Manager'],
      careerProgression: 'Consistent data engineering trajectory.'
    },
    contactHistory: [],
    uploadedAt: '2026-07-26 11:00'
  }
];

export const INITIAL_TIMELINE_EVENTS: Record<string, TimelineEvent[]> = {
  'cand-1': [
    {
      id: 'time-1',
      candidateId: 'cand-1',
      type: 'UPLOAD',
      title: 'Resume Uploaded & Parsed',
      description: 'Parsed using PyMuPDF & Local Ollama Qwen model',
      timestamp: '2026-07-25 14:30'
    },
    {
      id: 'time-2',
      candidateId: 'cand-1',
      type: 'MATCHED',
      title: 'Matched with Job Requirement',
      description: 'Matched with "Senior PMO Executive / Delivery Lead" (Score: 88%)',
      timestamp: '2026-07-25 15:10'
    },
    {
      id: 'time-3',
      candidateId: 'cand-1',
      type: 'CONTACTED',
      title: 'Candidate Contacted',
      description: 'Phone call logged by Recruiter',
      timestamp: '2026-07-25 16:45'
    }
  ],
  'cand-2': [
    {
      id: 'time-4',
      candidateId: 'cand-2',
      type: 'UPLOAD',
      title: 'Resume Uploaded & Parsed',
      description: 'PDF parse complete with deterministic contact extraction',
      timestamp: '2026-07-26 10:15'
    },
    {
      id: 'time-5',
      candidateId: 'cand-2',
      type: 'MATCHED',
      title: 'Matched with Job Requirement',
      description: 'Matched with "Sr. Java Backend Developer (Banking Domain)" (Score: 94%)',
      timestamp: '2026-07-26 10:20'
    }
  ]
};

export const INITIAL_NOTES: Record<string, RecruiterNote[]> = {
  'cand-1': [
    {
      id: 'note-1',
      candidateId: 'cand-1',
      content: 'Candidate contacted for PMO opening. Expressed willingness to join in 30 days. High communication confidence.',
      createdAt: '2026-07-25 16:45',
      author: 'Recruiter Workspace'
    }
  ]
};

export const INITIAL_REPORT_STATS: AppReportStats = {
  totalCandidates: 148,
  newResumesThisWeek: 24,
  activeRequirements: 6,
  topMatchesCount: 38,
  candidatesContacted: 19,
  avgMatchScore: 82,
  skillsDistribution: [
    { name: 'Power BI', count: 42 },
    { name: 'SQL', count: 86 },
    { name: 'Java', count: 54 },
    { name: 'Spring Boot', count: 48 },
    { name: 'PMO', count: 28 },
    { name: 'Python', count: 62 },
    { name: 'PostgreSQL', count: 45 }
  ],
  experienceDistribution: [
    { range: '0-2 Years', count: 22 },
    { range: '2-5 Years', count: 68 },
    { range: '5-8 Years', count: 40 },
    { range: '8+ Years', count: 18 }
  ],
  uploadActivity: [
    { date: 'Mon', uploads: 4 },
    { date: 'Tue', uploads: 7 },
    { date: 'Wed', uploads: 5 },
    { date: 'Thu', uploads: 9 },
    { date: 'Fri', uploads: 12 },
    { date: 'Sat', uploads: 6 },
    { date: 'Sun', uploads: 3 }
  ]
};
