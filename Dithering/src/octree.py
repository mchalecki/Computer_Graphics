from src.color import Color


class OctreeNode(object):

    def __init__(self, level, parent):
        self.color = Color(0, 0, 0)
        self.pixel_count = 0
        self.palette_index = 0
        self.children = [None for _ in range(8)]
        # add node to current level
        if level < OctreeQuantizer.MAX_DEPTH - 1:
            parent.add_level_node(level, self)

    def is_leaf(self):
        return self.pixel_count > 0

    def get_all_leaf_nodes(self):
        leaf_nodes = []
        for i in range(8):
            node = self.children[i]
            if node:
                if node.is_leaf():
                    leaf_nodes.append(node)
                else:
                    leaf_nodes.extend(node.get_all_leaf_nodes())
        return leaf_nodes

    def add_color(self, color, level, parent):
        if level >= OctreeQuantizer.MAX_DEPTH:
            self.color.red += color.red
            self.color.green += color.green
            self.color.blue += color.blue
            self.pixel_count += 1
            return
        index = self.get_color_index_for_level(color, level)
        if not self.children[index]:
            self.children[index] = OctreeNode(level, parent)
        self.children[index].add_color(color, level + 1, parent)

    def get_palette_index(self, color, level):
        """
        Get palette index for `color`
        Uses `level` to go one level deeper if the node is not a leaf
        """
        if self.is_leaf():
            return self.palette_index
        index = self.get_color_index_for_level(color, level)
        if self.children[index]:
            return self.children[index].get_palette_index(color, level + 1)
        else:
            # get palette index for a first found child node
            for i in range(8):
                if self.children[i]:
                    return self.children[i].get_palette_index(color, level + 1)

    def remove_leaves(self):
        """
        Add all children pixels count and color channels to parent node 
        Return the number of removed leaves
        """
        result = 0
        for i in range(8):
            node = self.children[i]
            if node:
                self.color.red += node.color.red
                self.color.green += node.color.green
                self.color.blue += node.color.blue
                self.pixel_count += node.pixel_count
                result += 1
        return result - 1

    def get_average_color(self):
        return Color(
            self.color.red / self.pixel_count,
            self.color.green / self.pixel_count,
            self.color.blue / self.pixel_count)

    @staticmethod
    def get_color_index_for_level(color, level):
        """
        Get index of `color` for next `level`
        """
        index = 0
        mask = 0x80 >> level
        if color.red & mask:
            index |= 4
        if color.green & mask:
            index |= 2
        if color.blue & mask:
            index |= 1
        return index


class OctreeQuantizer(object):
    MAX_DEPTH = 8

    def __init__(self):
        self.levels = {i: [] for i in range(OctreeQuantizer.MAX_DEPTH)}
        self.root = OctreeNode(0, self)

    def get_leaves(self):
        return [node for node in self.root.get_all_leaf_nodes()]

    def add_level_node(self, level, node):
        self.levels[level].append(node)

    def add_color(self, color):
        # passes self value as `parent` to save nodes to levels dict
        self.root.add_color(color, 0, self)

    def make_palette(self, color_count):
        palette = []
        palette_index = 0
        leaf_count = len(self.get_leaves())
        # reduce nodes
        # up to 8 leaves can be reduced here and the palette will have
        # only 248 colors (in worst case) instead of expected 256 colors
        for level in range(OctreeQuantizer.MAX_DEPTH - 1, -1, -1):
            if self.levels[level]:
                for node in self.levels[level]:
                    leaf_count -= node.remove_leaves()
                    if leaf_count <= color_count:
                        break
                if leaf_count <= color_count:
                    break
                self.levels[level] = []
        # build palette
        for node in self.get_leaves():
            if palette_index >= color_count:
                break
            if node.is_leaf():
                palette.append(node.get_average_color())
            node.palette_index = palette_index
            palette_index += 1
        return palette

    def get_palette_index(self, color):
        return self.root.get_palette_index(color, 0)
