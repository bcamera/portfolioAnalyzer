from django.shortcuts import render
from django.utils import timezone
from .models import Post
from django.shortcuts import render, get_object_or_404
from .forms import PostForm
from django.shortcuts import redirect
from django.contrib import messages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import pylab
from pylab import *
import PIL, PIL.Image
from io import BytesIO

import pandas_datareader as web
from pandas_datareader._utils import RemoteDataError
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
    listaInvalido = list()
    listaInexistente = list()
    for i in acoes:
        tickerAtual = (i.strip()+'.SA')
        #print(tickerAtual)
        listaAcoes.append(i.strip()+'.SA')
        try:
            dados = web.get_data_yahoo(tickerAtual, start, end)['Adj Close']
            if dados.count() < 400:
                listaAcoes.remove(i.strip()+'.SA')
                #messages.warning(request,'Código(s) sem histórico removido da análise '+i )
                if (len(listaInvalido) == 0):
                    listaInvalido.append(i.strip())
                else:
                    listaInvalido.append(i.strip())
                #print(i)
        except RemoteDataError:
            listaAcoes.remove(i.strip()+'.SA')
            if (len(listaInexistente) == 0):
                    listaInexistente.append(i.strip())
            else:
                    listaInexistente.append(i.strip())
            #messages.warning(request,'Código(s) inválido removido da análise'+i )
            continue

    
    acoes = listaAcoes
    #print(acoes)
    dados = (web.get_data_yahoo(acoes, start, end)['Adj Close'])
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

    #transformar nosso dicionário em um dataframe
    df = pd.DataFrame(carteira)

    #nomear as colunas do novo dataframe
    colunas = ['Retorno', 'Volatilidade', 'Sharpe Ratio'] + [acao+' Peso' for acao in acoes]
    df = df[colunas]
    
    #identificar as variáveis de interesse
    menor_volatilidade = df['Volatilidade'].min()
    maior_sharpe = df['Sharpe Ratio'].max()

    #identificar os dois principais portfolios
    carteira_sharpe = df.loc[df['Sharpe Ratio'] == maior_sharpe]
    carteira_min_variancia = df.loc[df['Volatilidade'] == menor_volatilidade]

    # plot frontier, max sharpe & min Volatility values with a scatterplot
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(nrows=4, ncols=1)
    plt.style.use('seaborn-dark')
    
    # chart 1 plot
    df.plot.scatter(x='Volatilidade', y='Retorno', c='Sharpe Ratio',
                    cmap='RdYlGn', edgecolors='black', figsize=(11, 18), grid=True, ax=ax2)
    ax2.scatter(x=carteira_sharpe['Volatilidade'], y=carteira_sharpe['Retorno'], c='red', marker='o', s=200)
    ax2.scatter(x=carteira_min_variancia['Volatilidade'], y=carteira_min_variancia['Retorno'], c='blue', marker='o', s=200)
    ax2.set_xlabel('Volatilidade')
    ax2.set_ylabel('Retorno Esperado')

    ax2.legend(loc='best', shadow=True, fontsize='x-large', labels=('Mínima Variância','Maior Risco x Retorno'))

    #Grafico Minima Variancia
    minimo = carteira_min_variancia['Retorno']
    minimo = minimo.tolist()
    risco = carteira_sharpe['Retorno']
    risco = risco.tolist()

    acaoMinRisc = []
    for j in acoes:
      acaoMinRisc.extend(carteira_min_variancia[j+' Peso'].tolist())
    map(float,acaoMinRisc)
    data2 = [round(k,4) for k in acaoMinRisc]
    data = [str(d) for d in data2]

    recipe = []
    for a,b in zip(acoes,data):
        recipe.append(a+' '+b)
        
    #ax2 = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))    

    data = [float(x.split()[1]) for x in recipe]
    ingredients = [x.split()[0] for x in recipe]

    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.2f}%".format(pct, absolute)

    #chart 2 plot
    wedges, texts, autotexts = ax3.pie(data, autopct=lambda pct: func(pct, data),
                                      textprops=dict(color="w"))

    ax3.legend(wedges, ingredients,
              title="Ações",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))

    #plt.setp(autotexts, size=8, weight="bold")

    ax3.set_title("Mínima Variância")


    #Grafico Maior Sharpe Rate
    acaoMaiorRisc = []
    for j in acoes:
      acaoMaiorRisc.extend(carteira_sharpe[j+' Peso'].tolist())
    map(float,acaoMaiorRisc)
    data3 = [round(k,4) for k in acaoMaiorRisc]
    data4 = [str(d) for d in data3]


    recipe_Sharpe = []
    for a,b in zip(acoes,data4):
        recipe_Sharpe.append(a+' '+b)
        
    #ax2 = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))    

    data4 = [float(x.split()[1]) for x in recipe_Sharpe]
    ingredients_sharpe = [x.split()[0] for x in recipe_Sharpe]

    def func(pct, allvals):
        absolute = int(pct/100.*np.sum(allvals))
        return "{:.2f}%".format(pct, absolute)


    #chart 3 plot
    wedges, texts, autotexts = ax4.pie(data4, autopct=lambda pct: func(pct, data4),
                                      textprops=dict(color="w"))
    ax4.legend(wedges, ingredients_sharpe,
              title="Ações",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))

    #plt.setp(autotexts, size=8, weight="bold")

    ax4.set_title("Maior Retorno")

    #chart 4 plot
    ax1.text(0.5, 1.0, 'Relatório da análise da carteira', size=24, ha='center', va='top')
    if (len(listaInexistente) > 0) or (len(listaInvalido) > 0):
        ax1.text(0.0, 0.8, 'Os seguintes códigos foram removidos da análise:', size=10, color='red', ha='left', va='top')
        ax1.text(0.0, 0.7, 'Código(s) inválidos:'+str(listaInexistente)[1:-1], size=10, color='red', ha='left', va='top')
        ax1.text(0.0, 0.6, 'Código(s) sem histórico suficiente:'+str(listaInvalido)[1:-1], size=10, color='red', ha='left', va='top')
    ax1.text(0.0, 0.5, 'A carteira a ser analisada é composta de '+str(len(listaAcoes))+' ações, sendo que durante o período analisado, tivemos um retorno anual de ' +str(round(carteira_min_variancia['Retorno']*100,2)).split('\n',1)[0].split(' ',1)[1].strip()+'%.', size=10, ha='left', va='top')
    ax1.text(0.0, 0.3, 'Já na carteira com o maior risco e retorno esperado, tivemos um retorno anual de ' +str(round(carteira_sharpe['Retorno']*100,2)).split('\n',1)[0].split(' ',1)[1].strip()+'%, tomando como base o ponto', size=10, ha='left', va='top')
    ax1.text(0.0, 0.4, 'tomando como base o ponto azul no gráfico abaixo, que é a carteira de menor risco, ou seja menor variação de preços.', size=10, ha='left', va='top')
    ax1.text(0.0, 0.2, 'vermelho no gráfico abaixo, que é a carteira de maior risco e retorno esperado.', size=10, ha='left', va='top')
    #ax1.text(0.5, 1.0, '', size=24, ha='center', va='top')
    #ax1.text(0.5, 1.0, 'Análise da carteira', size=24, ha='center', va='top')
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    #removing labels
    ax1.spines['bottom'].set_visible(False)
    ax1.set_xticklabels([])
    ax1.set_xticks([])
    ax1.axes.get_xaxis().set_visible(False)
    ax1.spines['left'].set_visible(False)
    ax1.set_yticklabels([])
    ax1.set_yticks([])
    ax1.axes.get_yaxis().set_visible(False)
    ax1.set_axis_off()
    
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
    
def post_detail(request):
    post = get_object_or_404(Post)
    return render(request, 'blog/index.html', {'post': post})
    
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
