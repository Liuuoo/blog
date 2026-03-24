#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

// 快速排序算法实现
void quickSort(vector<int>& arr, int left, int right) {
    if (left >= right) return;
    
    int pivot = arr[left + (right - left) / 2];
    int i = left, j = right;
    
    while (i <= j) {
        while (arr[i] < pivot) i++;
        while (arr[j] > pivot) j--;
        if (i <= j) {
            swap(arr[i], arr[j]);
            i++;
            j--;
        }
    }
    
    quickSort(arr, left, j);
    quickSort(arr, i, right);
}

int main() {
    vector<int> data = {9, -3, 5, 2, 6, 8, -6, 1, 3};
    
    cout << "排序前: ";
    for (int n : data) cout << n << " ";
    cout << endl;
    
    quickSort(data, 0, data.size() - 1);
    
    cout << "排序后: ";
    for (int n : data) cout << n << " ";
    cout << endl;
    
    return 0;
}
