import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Check, X } from 'lucide-react';
import Image from 'next/image';

interface Product {
  id: string;
  title: string;
  image_url: string;
  price: number;
  category?: string;
  tags?: string[];
}

interface ProductCardProps {
  product: Product;
  onFeedback: (productId: string, feedback: 'approved' | 'rejected') => void;
}

export default function ProductCard({ product, onFeedback }: ProductCardProps) {
  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <div className="relative aspect-square">
        <Image
          src={product.image_url}
          alt={product.title}
          fill
          className="object-cover"
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        />
      </div>
      <CardContent className="p-4">
        <h3 className="font-semibold text-sm mb-2 line-clamp-2">{product.title}</h3>
        <p className="text-lg font-bold text-green-600 mb-3">${product.price.toFixed(2)}</p>
        {product.category && (
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
            {product.category}
          </span>
        )}
        <div className="flex gap-2 mt-4">
          <Button
            onClick={() => onFeedback(product.id, 'approved')}
            size="sm"
            className="flex-1 bg-green-600 hover:bg-green-700"
          >
            <Check className="h-4 w-4 mr-1" />
            Approve
          </Button>
          <Button
            onClick={() => onFeedback(product.id, 'rejected')}
            size="sm"
            variant="destructive"
            className="flex-1"
          >
            <X className="h-4 w-4 mr-1" />
            Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
