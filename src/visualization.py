import seaborn as sns
import matplotlib.pyplot as plt
from consts import *


def plot_hist(data, title, xlabel, ylabel, figsize=(10, 5), bins=20):
    plt.figure(figsize=figsize)
    sns.histplot(data, bins=bins)
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.show()
    
def plot_roofs(groups, color_column_name, orientation_column_name, figsize=(4,4)):
    for id, group in groups:
        fig, axes = plt.subplots()
        fig.set_size_inches(figsize)
        group.plot(ax=axes, color=group[color_column_name], alpha=0.5, legend=True)
        axes.set_title(f"{group[ADDRESS].iloc[0]}")
        axes.ticklabel_format(useOffset=False, style='plain')
        axes.set_xlabel("Y, m")
        axes.set_ylabel("X, m")
        axes.tick_params(axis='x', labelrotation=45)

        handles = []
        labels = []
        for item in group.iterrows():
            name = item[1][orientation_column_name]
            color = item[1][color_column_name]
            if (name not in labels):
                handles.append(plt.Rectangle((0, 0), 1, 1, fc=color, alpha=0.5))
                labels.append(name)
        
        fig.legend(handles, labels, title='Orientation', frameon=True)

        plt.show()

def plot_empty_files_bar_graph(years, empty_files_numbers, files_numbers, title):
    year_labels = []
    empty_percentage = []

    for year in years:
        percentage = empty_files_numbers[year] / files_numbers[year] * 100
        empty_percentage.append(percentage)
        year_labels.append(str(year))
        
    empty_percentage.reverse()
    year_labels.reverse()
    
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize =(8, 3))

    sns.barplot(x=empty_percentage, y=year_labels, palette='viridis_r')

    for index, value in enumerate(empty_percentage):
        plt.text(value + 1, index, f'{value:.2f}%', va='center', fontsize=12)

    sns.despine(left=True, bottom=True)
    plt.gca().invert_yaxis()

    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')

    ax.xaxis.set_tick_params(pad = 5)
    ax.yaxis.set_tick_params(pad = 10)

    plt.title(title, fontsize=14)
    plt.xlabel('Percentage of empty files', fontsize=12)
    plt.ylabel('Year', fontsize=12)
    plt.tight_layout()
    plt.show()