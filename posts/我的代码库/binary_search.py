def binary_search(arr, target):
    """
    二分查找算法实现
    :param arr: 有序数组
    :param target: 目标值
    :return: 目标值索引，未找到返回 -1
    """
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid_idx = (left + right) // 2
        mid_val = arr[mid_idx]
        
        if mid_val == target:
            return mid_idx
        elif mid_val < target:
            left = mid_idx + 1
        else:
            right = mid_idx - 1
            
    return -1

if __name__ == '__main__':
    data = [1, 3, 5, 7, 9, 11, 13, 15]
    search_for = 7
    result = binary_search(data, search_for)
    
    if result != -1:
        print(f"找到元素 {search_for}，索引位置: {result}")
    else:
        print(f"未找到元素 {search_for}")
