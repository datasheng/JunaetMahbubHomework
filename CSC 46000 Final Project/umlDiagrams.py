import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch

# ================================================
# 1. Data Model Diagram (UML Class Diagram)
# ================================================
def generate_uml_class_diagram():
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_title("StockData Class Diagram (UML)", fontsize=14, pad=20)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Draw the class box
    class_box = patches.Rectangle((2, 2), 6, 6, linewidth=2, edgecolor='black', facecolor='white')
    ax.add_patch(class_box)

    # Class name
    plt.text(5, 7.5, 'StockData', ha='center', va='center', fontsize=12, weight='bold')

    # Attributes
    attributes = [
        '- date: Date',
        '- open: float',
        '- high: float',
        '- low: float',
        '- close: float',
        '- volume: int',
        '- ticker: str'
    ]
    y_pos = 6.5
    for attr in attributes:
        plt.text(5, y_pos, attr, ha='center', va='center', fontsize=10)
        y_pos -= 0.5

    plt.savefig('uml_class_diagram.png')
    plt.close()

# ================================================
# 2. Data Flow Diagram (DFD - Level 1)
# ================================================
def generate_data_flow_diagram():
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_title("Stock Data Flow Diagram (Level 1)", fontsize=14, pad=20)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Define positions for components
    components = {
        'Data Source\n(e.g., CSV/API)': (1, 4),
        'Ingest Raw Data': (3, 4),
        'Validate &\nClean Data': (5, 4),
        'Stock Database': (7, 6),
        'Error Logs': (7, 2),
        'Generate Output': (9, 4),
        'End User\n(Analyst/App)': (11, 4)
    }

    # Draw components as rectangles
    for name, (x, y) in components.items():
        rect = patches.Rectangle((x-1, y-0.5), 2, 1, linewidth=1, edgecolor='black', facecolor='lightgray')
        ax.add_patch(rect)
        plt.text(x, y, name, ha='center', va='center', fontsize=10)

    # Draw data flow arrows
    arrows = [
        ('Data Source\n(e.g., CSV/API)', 'Ingest Raw Data'),
        ('Ingest Raw Data', 'Validate &\nClean Data'),
        ('Validate &\nClean Data', 'Stock Database'),
        ('Validate &\nClean Data', 'Error Logs'),
        ('Stock Database', 'Generate Output'),
        ('Generate Output', 'End User\n(Analyst/App)')
    ]

    for start, end in arrows:
        start_x, start_y = components[start]
        end_x, end_y = components[end]
        arrow = FancyArrowPatch(
            (start_x + 0.5, start_y),
            (end_x - 0.5, end_y),
            arrowstyle='->',
            mutation_scale=20,
            linewidth=1.5,
            color='blue'
        )
        ax.add_patch(arrow)

    plt.savefig('data_flow_diagram.png')
    plt.close()

# ================================================
# Run the script and display diagrams
# ================================================
if __name__ == "__main__":
    generate_uml_class_diagram()
    generate_data_flow_diagram()
    
    # Display the generated diagrams
    uml_img = plt.imread('uml_class_diagram.png')
    dfd_img = plt.imread('data_flow_diagram.png')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
    ax1.imshow(uml_img)
    ax1.axis('off')
    ax2.imshow(dfd_img)
    ax2.axis('off')
    plt.show()