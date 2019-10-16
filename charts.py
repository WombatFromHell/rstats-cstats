from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt

USAGE_CAP=(10**12) # 1 TB (Default)

def get_size(num, pos=0, suffix='B'):
    # https://stackoverflow.com/a/1094933
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def get_size_mebi(num):
    return num / 2**20

def create_daily_barh_chart(dumped_stats):
    fig, ax = plt.subplots(figsize=(8,12))
    ax2 = ax.twinx() # right hand Y-axis ticks

    formatter = FuncFormatter(get_size)
    ax.yaxis.set_major_formatter(formatter)
    x_labels = dumped_stats["DAYS"]["x_labels"]
    y_labels = dumped_stats["DAYS"]["y_labels"]
    y_vals = dumped_stats["DAYS"]["y"]
    y_pos = range(len(y_vals))

    # show grid lines for ease of reading
    ax.grid(b=True, axis='both', linestyle='dashed', zorder=3)
    ax.set_axisbelow(b=True)
    # set labels for the left-hand ticks
    ax.set_yticks(y_pos)
    ax.set_yticklabels(x_labels)
    # set labels for the right-hand ticks
    ax2.set_yticks(y_pos)
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticklabels(y_labels)
    # set the chart format
    plt.barh(y_pos, y_vals, align='center')
    plt.yticks(y_pos, y_labels)
    # show a cumulative total of the last 30 days in our x-label
    cum_total = sum(x for x in dumped_stats["DAYS"]["y"][-1:-30:-1])
    #plt.xlabel("Bandwidth Usage ({0})".format(get_size(cum_total)))
    ax.set_xlabel("Bandwidth Usage ({0})".format(get_size(cum_total)))

    # scale the figure to fit the output and save to png
    fig.tight_layout()
    plt.savefig("rstats-daily.png", bbox_inches='tight', format="png")

def create_daily_bar_chart(dumped_stats):
    fig, ax = plt.subplots(figsize=(20,3))
    formatter = FuncFormatter(get_size)
    ax.yaxis.set_major_formatter(formatter)
    x_labels = dumped_stats["DAYS"]["x_labels"]
    y_labels = dumped_stats["DAYS"]["y_labels"]
    y_vals = dumped_stats["DAYS"]["y"]
    x_pos = range(len(y_vals))
    # show grid lines for ease of reading
    ax.grid(b=True, axis='y', linestyle='dashed', zorder=3)
    ax.set_axisbelow(b=True)
    # set the chart format
    plt.bar(x_pos, y_vals, width=0.85, align='center')
    plt.xticks(x_pos, y_labels, fontsize='9')
    # show a cumulative total of the last 30 days in our x-label
    cum_total = sum(x for x in dumped_stats["DAYS"]["y"][-1:-30:-1])
    plt.xlabel("Bandwidth Usage ({0})".format(get_size(cum_total)))
    # scale the figure to fit the output and save to png
    fig.tight_layout()
    plt.savefig("rstats-daily.png", bbox_inches='tight', format="png")

def create_monthly_usage_chart(dumped_stats, cap_bytes=USAGE_CAP):
    # use the most recent slice of 30 days
    bytes = sum(x for x in dumped_stats["DAYS"]["y"][-1:-30:-1])
    # compare against the given
    usage =  get_size_mebi(bytes) / get_size_mebi(cap_bytes) * 100 # percentage of cap
    remain = 100 - usage
    # set the schema for the pie chart
    labels = "{0} used".format(get_size(bytes)), 'Remaining'
    nums = [ usage, remain ]
    explode = (0.1, 0)
    fig, ax = plt.subplots()
    ax.axis('equal')
    ax.set_title("Bandwidth usage ({0} cap)".format(get_size(cap_bytes)))
    ax.pie(nums, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True, startangle=120)
    plt.savefig("rstats-usage.png", bbox_inches='tight', format="png")