"""
Admin Dashboard - Help Articles Views
Handles CRUD operations for help articles and categories
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.text import slugify
from core.models import HelpArticle, HelpCategory


@staff_member_required
def help_article_list(request):
    """List all help articles with filtering and pagination"""
    articles = HelpArticle.objects.select_related('category').all()
    
    # Apply filters
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if category_filter:
        articles = articles.filter(category_id=category_filter)
    
    if status_filter == 'published':
        articles = articles.filter(is_published=True)
    elif status_filter == 'draft':
        articles = articles.filter(is_published=False)
    
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(articles, 20)
    page_number = request.GET.get('page')
    articles_page = paginator.get_page(page_number)
    
    # Statistics
    total_articles = HelpArticle.objects.count()
    published_articles = HelpArticle.objects.filter(is_published=True).count()
    draft_articles = HelpArticle.objects.filter(is_published=False).count()
    total_views = HelpArticle.objects.aggregate(total=Count('views'))['total'] or 0
    
    # Categories for filter dropdown
    categories = HelpCategory.objects.all()
    
    context = {
        'articles': articles_page,
        'categories': categories,
        'total_articles': total_articles,
        'published_articles': published_articles,
        'draft_articles': draft_articles,
        'total_views': total_views,
    }
    
    return render(request, 'admin_dashboard/help_articles/list.html', context)


@staff_member_required
def help_article_detail(request, article_id):
    """View article details"""
    article = get_object_or_404(HelpArticle, id=article_id)
    
    # Get related articles from the same category
    related_articles = HelpArticle.objects.filter(
        category=article.category
    ).exclude(id=article.id)[:5]
    
    context = {
        'article': article,
        'related_articles': related_articles,
    }
    
    return render(request, 'admin_dashboard/help_articles/detail.html', context)


@staff_member_required
def help_article_add(request):
    """Add new article"""
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug') or slugify(title)
        category_id = request.POST.get('category')
        content = request.POST.get('content')
        is_published = request.POST.get('is_published') == 'on'
        
        try:
            category = HelpCategory.objects.get(id=category_id)
            article = HelpArticle.objects.create(
                title=title,
                slug=slug,
                category=category,
                content=content,
                is_published=is_published
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'article_id': article.id
                })
            
            return redirect('admin_dashboard:help_article_detail', article_id=article.id)
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
            return redirect('admin_dashboard:help_article_list')
    
    categories = HelpCategory.objects.all()
    context = {
        'categories': categories,
    }
    
    return render(request, 'admin_dashboard/help_articles/form.html', context)


@staff_member_required
def help_article_edit(request, article_id):
    """Edit existing article"""
    article = get_object_or_404(HelpArticle, id=article_id)
    
    if request.method == 'POST':
        article.title = request.POST.get('title')
        article.slug = request.POST.get('slug') or slugify(article.title)
        category_id = request.POST.get('category')
        article.content = request.POST.get('content')
        article.is_published = request.POST.get('is_published') == 'on'
        
        try:
            article.category = HelpCategory.objects.get(id=category_id)
            article.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'article_id': article.id
                })
            
            return redirect('admin_dashboard:help_article_detail', article_id=article.id)
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                })
    
    categories = HelpCategory.objects.all()
    context = {
        'article': article,
        'categories': categories,
    }
    
    return render(request, 'admin_dashboard/help_articles/form.html', context)


@staff_member_required
def help_article_delete(request, article_id):
    """Delete article"""
    if request.method == 'POST':
        try:
            article = get_object_or_404(HelpArticle, id=article_id)
            article.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Article deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@staff_member_required
def help_article_duplicate(request, article_id):
    """Duplicate an article"""
    if request.method == 'POST':
        try:
            original_article = get_object_or_404(HelpArticle, id=article_id)
            
            # Create a copy
            new_article = HelpArticle.objects.create(
                title=f"{original_article.title} (Copy)",
                slug=f"{original_article.slug}-copy",
                category=original_article.category,
                content=original_article.content,
                is_published=False  # Always create as draft
            )
            
            return JsonResponse({
                'success': True,
                'new_article_id': new_article.id,
                'message': 'Article duplicated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@staff_member_required
def help_article_bulk_delete(request):
    """Bulk delete articles"""
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            article_ids = data.get('article_ids', [])
            
            HelpArticle.objects.filter(id__in=article_ids).delete()
            
            return JsonResponse({
                'success': True,
                'message': f'{len(article_ids)} article(s) deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@staff_member_required
def help_article_export(request):
    """Export articles to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="help_articles.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Title', 'Category', 'Status', 'Views', 'Created', 'Updated'])
    
    articles = HelpArticle.objects.select_related('category').all()
    for article in articles:
        writer.writerow([
            article.title,
            article.category.name,
            'Published' if article.is_published else 'Draft',
            article.views,
            article.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            article.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response


# Category Management Views

@staff_member_required
def help_category_list(request):
    """List all help categories"""
    categories = HelpCategory.objects.annotate(
        article_count=Count('articles')
    ).order_by('order', 'name')
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'admin_dashboard/help_articles/categories.html', context)


@staff_member_required
def help_category_add(request):
    """Add new category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug') or slugify(name)
        icon = request.POST.get('icon')
        description = request.POST.get('description', '')
        order = request.POST.get('order', 0)
        
        try:
            category = HelpCategory.objects.create(
                name=name,
                slug=slug,
                icon=icon,
                description=description,
                order=order
            )
            
            return redirect('admin_dashboard:help_category_list')
        except Exception as e:
            # Handle error - you might want to add error messages here
            return redirect('admin_dashboard:help_category_add')
    
    return render(request, 'admin_dashboard/help_articles/category_form.html')


@staff_member_required
def help_category_edit(request, category_id):
    """Edit existing category"""
    category = get_object_or_404(HelpCategory, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = request.POST.get('slug') or slugify(category.name)
        category.icon = request.POST.get('icon')
        category.description = request.POST.get('description', '')
        category.order = request.POST.get('order', 0)
        
        try:
            category.save()
            return redirect('admin_dashboard:help_category_list')
        except Exception as e:
            # Handle error
            pass
    
    context = {
        'category': category,
    }
    
    return render(request, 'admin_dashboard/help_articles/category_form.html', context)


@staff_member_required
def help_category_delete(request, category_id):
    """Delete category"""
    if request.method == 'POST':
        try:
            category = get_object_or_404(HelpCategory, id=category_id)
            
            # Check if category has articles
            if category.articles.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Cannot delete category with articles. Please reassign or delete articles first.'
                })
            
            category.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Category deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })
