"use client";

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { 
  DollarSign, ShoppingCart, TrendingUp, Palette, AlertCircle, RefreshCw, 
  Zap, Info, Brain, Image as ImageIcon, ExternalLink, LayoutGrid, 
  Check, X, Trash2, Rocket, Calendar, Settings, Target, Package, ThumbsUp, ThumbsDown
} from 'lucide-react';
import { Toaster, toast } from 'sonner';

// Interfaces
interface DashboardStats {
  revenue: number;
  orders: number;
  products: number;
  trends: number;
}

interface Artwork {
  image_url: string | null;
  style: string | null;
  provider: string | null;
  quality_score: number;
  model_used: string | null;
}

interface Product {
  id: number;
  title: string;
  sku: string;
  status: string;
  base_price: number;
  description?: string;
  artwork?: Artwork | null;
}

interface GenerationStatus {
  total_products: number;
  trends_with_products: number;
  total_artwork: number;
  trends_awaiting_generation: number;
}

interface TrendAnalytics {
  total_trends: number;
  total_categories: number;
  avg_trend_score: number;
  goal_progress: {
    target_designs: number;
    current_designs: number;
    designs_needed: number;
    trends_needed: number;
    progress_percentage: number;
  };
  top_categories: Array<{
    name: string;
    count: number;
    avg_score: number;
  }>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentProducts, setRecentProducts] = useState<Product[]>([]);
  const [genStatus, setGenStatus] = useState<GenerationStatus | null>(null);
  const [trendAnalytics, setTrendAnalytics] = useState<TrendAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isFetchingTrends, setIsFetchingTrends] = useState(false);
  const [isLaunching10K, setIsLaunching10K] = useState(false);
  const [showGallery, setShowGallery] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());
  
  // Track hidden products across refreshes using useRef
  const hiddenProductIds = useRef<Set<number>>(new Set());
  
  // Generation settings
  const [budgetMode, setBudgetMode] = useState<'cheap' | 'balanced' | 'quality'>('balanced');
  const [testingMode, setTestingMode] = useState(true);
  const [trendsToGenerate, setTrendsToGenerate] = useState(10);
  const [dailyGenerationTarget, setDailyGenerationTarget] = useState(100);
  const [autoGeneration, setAutoGeneration] = useState(false);

  // Fetch dashboard data
  const fetchData = async () => {
    // Define API_URL here
    const API_URL = 'https://backend-production-7aae.up.railway.app/api/v1';
    
    if (!API_URL) {
      setError("API URL not configured");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      console.log('Fetching from API URL:', API_URL);

      const [statsResponse, productsResponse, genStatusResponse, analyticsResponse] = await Promise.all([
        fetch(`${API_URL}/analytics/dashboard`).catch(err => {
          console.error('Stats fetch failed:', err);
          return null;
        }),
        fetch(`${API_URL}/products/?limit=100&status=active&include_images=true`).catch(err => {
          console.error('Products fetch failed:', err);
          throw err;
        }),
        fetch(`${API_URL}/generation/status`).catch(err => {
          console.error('Gen status fetch failed:', err);
          return null;
        }),
        fetch(`${API_URL}/trends/analytics`).catch(err => {
          console.error('Analytics fetch failed:', err);
          return null;
        })
      ]);

      console.log('Responses received:', {
        stats: statsResponse?.status,
        products: productsResponse?.status,
        genStatus: genStatusResponse?.status,
        analytics: analyticsResponse?.status
      });

      if (statsResponse?.ok) {
        const statsData = await statsResponse.json();
        console.log('Stats data:', statsData);
        setStats({
          revenue: statsData.revenue || 0,
          orders: statsData.orders || 0,
          products: statsData.products || 0,
          trends: statsData.trends || 0,
        });
      }
      
      if (productsResponse?.ok) {
        const productsData = await productsResponse.json();
        console.log('Products response:', productsData);
        console.log('Products array length:', productsData.products?.length);
        
        // Filter out hidden products AND approved products
        const visibleProducts = (productsData.products || []).filter(
          (p: Product) => 
            p.status !== 'rejected' && 
            p.status !== 'approved' &&  // Don't show approved products
            !hiddenProductIds.current.has(p.id)
        );
        
        console.log('Visible products after filter:', visibleProducts.length);
        setRecentProducts(visibleProducts);
      } else {
        console.error('Products response not OK:', productsResponse?.status, productsResponse?
