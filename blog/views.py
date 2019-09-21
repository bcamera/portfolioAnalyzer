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

import pandas_datareader as web
from datetime import datetime
from django.http import HttpResponse

print_carteira_min_var = []

# Create your views here.
def carrega_dados(request, acao):
    start = datetime(2018, 1, 1)
    #end = datetime(2018, 12, 31)
    agora = datetime.now()
    end = agora.strftime('%Y/%m/%d')
    acao = acao.upper()
    acoes = acao.split(',')
    listaAcoes = list()
    for i in acoes:
       listaAcoes.append(i.strip()+'.SA')
    acoes = listaAcoes
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
    numero_carteiras = 10000
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
    
    # vamos identificar as variáveis de interesse
    menor_volatilidade = df['Volatilidade'].min()
    maior_sharpe = df['Sharpe Ratio'].max()

    # vamos identificar os dois principais portfolios
    carteira_sharpe = df.loc[df['Sharpe Ratio'] == maior_sharpe]
    carteira_min_variancia = df.loc[df['Volatilidade'] == menor_volatilidade]

    # plot frontier, max sharpe & min Volatility values with a scatterplot
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1)
    plt.style.use('seaborn-dark')
    df.plot.scatter(x='Volatilidade', y='Retorno', c='Sharpe Ratio',
                    cmap='RdYlGn', edgecolors='black', figsize=(14, 11), grid=True, ax=ax1)
    ax1.scatter(x=carteira_sharpe['Volatilidade'], y=carteira_sharpe['Retorno'], c='red', marker='o', s=200)
    ax1.scatter(x=carteira_min_variancia['Volatilidade'], y=carteira_min_variancia['Retorno'], c='blue', marker='o', s=200)
    ax1.set_xlabel('Volatilidade')
    ax1.set_ylabel('Retorno Esperado')

    ax1.legend(loc='best', shadow=True, fontsize='x-large', labels=('Mínima Variância','Maior Risco x Retorno'))

    minimo = carteira_min_variancia['Retorno']
    minimo = minimo.tolist()
    risco = carteira_sharpe['Retorno']
    risco = risco.tolist()

    acaoMinRisc = []
    for j in acoes:
      acaoMinRisc.extend(carteira_min_variancia[j+' Peso'].tolist())
    map(float,acaoMinRisc)
    data2 = [round(k,2) for k in acaoMinRisc]
    data = [str(d) for d in data2]

    recipe = []
    for a,b in zip(acoes,data):
        recipe.append(a+' '+b)
        
    #ax2 = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))    

    data = [float(x.split()[1]) for x in recipe]
    ingredients = [x.split()[0] for x in recipe]


    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.1f}%\n({:d} g)".format(pct, absolute)


    wedges, texts, autotexts = ax2.pie(data, autopct=lambda pct: func(pct, data),
                                      textprops=dict(color="w"))

    ax2.legend(wedges, ingredients,
              title="Ingredients",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))

    #plt.setp(autotexts, size=8, weight="bold")



    #data = [225, 90, 50, 60, 100, 5]
    #wedges, texts = ax2.pie(data, wedgeprops=dict(width=0.5), startangle=-40)
    #bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
    #kw = dict(arrowprops=dict(arrowstyle="-"),
#	          bbox=bbox_props, zorder=0, va="center")
	
    #for i, p in enumerate(wedges):
    #    ang = (p.theta2 - p.theta1)/2. + p.theta1
    #    y = np.sin(np.deg2rad(ang))
    #    x = np.cos(np.deg2rad(ang))
    #    horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
    #    connectionstyle = "angle,angleA=0,angleB={}".format(ang)
    #    kw["arrowprops"].update({"connectionstyle": connectionstyle})
    #    ax2.annotate(recipe[i], xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
    #                horizontalalignment=horizontalalignment, **kw)
	
    ax2.set_title("Mínima Variância")

    plt.show()

    #Constroi a imagem no buffer
    buffer = BytesIO()
    canvas = pylab.get_current_fig_manager().canvas
    canvas.draw()
    pilImage = PIL.Image.frombytes("RGB", canvas.get_width_height(), canvas.tostring_rgb())
    pilImage.save(buffer, "PNG")
    pylab.close()

    return HttpResponse(buffer.getvalue(), content_type="image/png")  
    
    #return render(request, 'blog/post_detail.html', {'acao1' : acao2 })
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
