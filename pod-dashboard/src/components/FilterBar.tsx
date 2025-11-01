import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search } from 'lucide-react';

interface Product {
  id: string;
  category?: string;
}

interface FilterBarProps {
  onFilterChange: (filters: {
    category?: string;
    priceRange?: [number, number];
    searchTerm?: string;
  }) => void;
  products: Product[];
}

export default function FilterBar({ onFilterChange, products }: FilterBarProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('all');

  const categories = ['all', ...Array.from(new Set(products.map(p => p.category).filter(Boolean)))];

  useEffect(() => {
    onFilterChange({
      category: category === 'all' ? undefined : category,
      searchTerm: searchTerm || undefined,
    });
  }, [searchTerm, category, onFilterChange]);

  return (
    <div className="flex flex-col md:flex-row gap-4 mb-6">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>
      <Select value={category} onValueChange={setCategory}>
        <SelectTrigger className="w-full md:w-[200px]">
          <SelectValue placeholder="Category" />
        </SelectTrigger>
        <SelectContent>
          {categories.map((cat, index) => (
            <SelectItem key={`category-${cat || 'all'}-${index}`} value={cat || 'all'}>
              {cat === 'all' ? 'All Categories' : cat}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
