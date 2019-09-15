from django.shortcuts import render
from django.utils import timezone
from .models import Post
from django.shortcuts import render, get_object_or_404
from .forms import PostForm
from django.shortcuts import redirect
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import pylab
from pylab import *
import PIL, PIL.Image
from io import BytesIO

#from io import StringIO

import pandas_datareader as web
from datetime import datetime
from django.http import HttpResponse

# Create your views here.
def carrega_dados(request, acao):
    start = datetime(2018, 1, 1)
    end = datetime(2018, 12, 31)
    acoes = ['PETR4.SA', 'VALE3.SA', 'UNIP6', 'FESA4.SA', 'BPAN4.SA']
    dados = web.get_data_yahoo(acoes, start, end)['Adj Close']
    descreva = dados.describe()

    # calculo dos retornos diários e anuais
    retorno_diario = dados.pct_change()
    retorno_anual = retorno_diario.mean() * 250

    cov_diaria = retorno_diario.cov()
    cov_anual = cov_diaria * 250
    retorno_carteira = []
    peso_acoes = []
    volatilidade_carteira = []
    sharpe_ratio = []
    numero_acoes = len(acoes)
    numero_carteiras = 1000
    np.random.seed(101)
    for cada_carteira in range(numero_carteiras):
        peso = np.random.random(numero_acoes)
        peso /= np.sum(peso)
        retorno = np.dot(peso, retorno_anual)
        volatilidade = np.sqrt(np.dot(peso.T, np.dot(cov_anual, peso)))
        sharpe = retorno / volatilidade
        sharpe_ratio.append(sharpe)
        retorno_carteira.append(retorno)
        volatilidade_carteira.append(volatilidade)
        peso_acoes.append(peso)

    carteira = {'Retorno': retorno_carteira,
             'Volatilidade': volatilidade_carteira,
             'Sharpe Ratio': sharpe_ratio}

    for contar,acao in enumerate(acoes):
        carteira[acao+' Peso'] = [Peso[contar] for Peso in peso_acoes]

    # vamos transformar nosso dicionário em um dataframe
    df = pd.DataFrame(carteira)

    # vamos nomear as colunas do novo dataframe
    colunas = ['Retorno', 'Volatilidade', 'Sharpe Ratio'] + [acao+' Peso' for acao in acoes]
    df = df[colunas]
    
    # plot frontier, max sharpe & min Volatility values with a scatterplot
    plt.style.use('seaborn-dark')
    df.plot.scatter(x='Volatilidade', y='Retorno', c='Sharpe Ratio',
                    cmap='RdYlGn', edgecolors='black', figsize=(10, 8), grid=True)
    plt.xlabel('Volatilidade')
    plt.ylabel('Retorno Esperado')
    plt.title('Fronteira Eficiente de Markowitz')

    buffer = BytesIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    pylab.close()

    return HttpResponse(buffer.getvalue(), content_type="image/png")
    #return render(request, 'blog/post_detail.html', {'acao' : response})
    #return HttpResponse(descreva)

def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')     
    return render(request, 'blog/post_list.html', {'posts': posts})
    
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})
    
def post_new(request):
     if request.method == "POST":
         form = PostForm(request.POST)
         if form.is_valid():
             post = form.save(commit=False) 
             post.author = request.user
             post.published_date = timezone.now()
             post.save()
             return redirect('post_detail', pk=post.pk)
     else:
         form = PostForm()
     return render(request, 'blog/post_edit.html', {'form': form})    
     
def post_edit(request, pk):
     post = get_object_or_404(Post, pk=pk)
     if request.method == "POST":
         form = PostForm(request.POST, instance=post)
         if form.is_valid():
             post = form.save(commit=False)
             post.author = request.user
             post.published_date = timezone.now()
             post.save()
             return redirect('post_detail', pk=post.pk)
     else:
         form = PostForm(instance=post)
     return render(request, 'blog/post_edit.html', {'form': form})     
