#include <vector>
#include <string>
#include <stdexcept>
#include <iostream>


struct IntArray {
    int64_t type_tag;  // 0 = int
    std::vector<int64_t> data;
};

extern "C" {
    IntArray* create_int_array(int64_t initial_size) {
        return new IntArray{0, std::vector<int64_t>(initial_size)};
    }

    void delete_int_array(IntArray* array) {
        delete array;
    }

    int64_t int_array_get(IntArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index];
    }

    void int_array_set(IntArray* array, int64_t index, int64_t value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = value;
    }

    void int_array_push_back(IntArray* array, int64_t value) {
        array->data.push_back(value);
    }

    // Get the size of the array
    int64_t int_array_size(IntArray* array) {
        return array->data.size();
    }

    int64_t int_array_remove(IntArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        int64_t removed = array->data[index];
        array->data.erase(array->data.begin() + index);
        return removed;
    }

    int64_t int_array_pop(IntArray* array) {
        if (array->data.empty()) {
            throw std::out_of_range("Array is empty");
        }
        int64_t removed = array->data.back();
        array->data.pop_back();
        return removed;
    }

    void int_array_insert(IntArray* array, int64_t index, int64_t value) {
        if (index < 0 || index > array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data.insert(array->data.begin() + index, value);
    }

    int64_t int_array_index_of(IntArray* array, int64_t value) {
        for (size_t i = 0; i < array->data.size(); ++i) {
            if (array->data[i] == value) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool int_array_equals(IntArray* a, IntArray* b) {
        if (a->data.size() != b->data.size()) return false;
        for (size_t i = 0; i < a->data.size(); ++i) {
            if (a->data[i] != b->data[i]) return false;
        }
        return true;
    }
}


struct FloatArray {
    int64_t type_tag;  // 1 = float
    std::vector<float> data;
};

extern "C" {
    FloatArray* create_float_array(int64_t initial_size) {
        return new FloatArray{1, std::vector<float>(initial_size)};
    }

    void delete_float_array(FloatArray* array) {
        delete array;
    }

    float float_array_get(FloatArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index];
    }

    void float_array_set(FloatArray* array, int64_t index, float value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = value;
    }

    void float_array_push_back(FloatArray* array, float value) {
        array->data.push_back(value);
    }

    // Get the size of the array
    int64_t float_array_size(FloatArray* array) {
        return array->data.size();
    }

    float float_array_remove(FloatArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }

        float removed = array->data[index];
        array->data.erase(array->data.begin() + index);
        return removed;
    }

    float float_array_pop(FloatArray* array) {
        if (array->data.empty()) {
            throw std::out_of_range("Array is empty");
        }
        float removed = array->data.back();
        array->data.pop_back();
        return removed;
    }

    void float_array_insert(FloatArray* array, int64_t index, float value) {
        if (index < 0 || index > array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data.insert(array->data.begin() + index, value);
    }

    int64_t float_array_index_of(FloatArray* array, float value) {
        for (size_t i = 0; i < array->data.size(); ++i) {
            if (array->data[i] == value) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool float_array_equals(FloatArray* a, FloatArray* b) {
        if (a->data.size() != b->data.size()) return false;
        for (size_t i = 0; i < a->data.size(); ++i) {
            if (a->data[i] != b->data[i]) return false;
        }
        return true;
    }
}


struct BoolArray {
    int64_t type_tag;  // 2 = bool
    std::vector<bool> data;
};

extern "C" {
    BoolArray* create_bool_array(int64_t initial_size) {
        return new BoolArray{2, std::vector<bool>(initial_size)};
    }

    void delete_bool_array(BoolArray* array) {
        delete array;
    }

    bool bool_array_get(BoolArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index];
    }

    void bool_array_set(BoolArray* array, int64_t index, bool value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = value;
    }

    void bool_array_push_back(BoolArray* array, bool value) {
        array->data.push_back(value);
    }

    // Get the size of the array
    int64_t bool_array_size(BoolArray* array) {
        return array->data.size();
    }

    bool bool_array_remove(BoolArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }

        bool removed = array->data[index];
        array->data.erase(array->data.begin() + index);
        return removed;
    }

    bool bool_array_pop(BoolArray* array) {
        if (array->data.empty()) {
            throw std::out_of_range("Array is empty");
        }
        bool removed = array->data.back();
        array->data.pop_back();
        return removed;
    }

    void bool_array_insert(BoolArray* array, int64_t index, bool value) {
        if (index < 0 || index > array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data.insert(array->data.begin() + index, value);
    }

    int64_t bool_array_index_of(BoolArray* array, bool value) {
        for (size_t i = 0; i < array->data.size(); ++i) {
            if (array->data[i] == value) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool bool_array_equals(BoolArray* a, BoolArray* b) {
        if (a->data.size() != b->data.size()) return false;
        for (size_t i = 0; i < a->data.size(); ++i) {
            if (a->data[i] != b->data[i]) return false;
        }
        return true;
    }
}


struct StringArray {
    int64_t type_tag;  // 3 = string
    std::vector<std::string> data;
};

extern "C" {
    StringArray* create_string_array(int64_t initial_size) {
        return new StringArray{3, std::vector<std::string>(initial_size)};
    }

    void delete_string_array(StringArray* array) {
        delete array;
    }

    const char* string_array_get(StringArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index].c_str();
    }

    void string_array_set(StringArray* array, int64_t index, const char* value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = std::string(value);
    }

    void string_array_push_back(StringArray* array, const char* value) {
        array->data.push_back(std::string(value));
    }

    // Get the size of the array
    int64_t string_array_size(StringArray* array) {
        return array->data.size();
    }

    const char* string_array_remove(StringArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }

        std::string removed = array->data[index];
        array->data.erase(array->data.begin() + index);
        // Return a copy of the removed string
        char* ret = new char[removed.size() + 1];
        std::strcpy(ret, removed.c_str());
        return ret;
    }

    const char* string_array_pop(StringArray* array) {
        if (array->data.empty()) {
            throw std::out_of_range("Array is empty");
        }
        std::string removed = array->data.back();
        array->data.pop_back();
        // Return a copy of the removed string
        char* ret = new char[removed.size() + 1];
        std::strcpy(ret, removed.c_str());
        return ret;
    }

    void string_array_insert(StringArray* array, int64_t index, const char* value) {
        if (index < 0 || index > array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data.insert(array->data.begin() + index, std::string(value));
    }

    int64_t string_array_index_of(StringArray* array, const char* value) {
        std::string val_str(value);
        for (size_t i = 0; i < array->data.size(); ++i) {
            if (array->data[i] == val_str) {
                return i;
            }
        }
        return -1;  // Not found
    }

    bool string_array_equals(StringArray* a, StringArray* b) {
        if (a->data.size() != b->data.size()) return false;
        for (size_t i = 0; i < a->data.size(); ++i) {
            if (a->data[i] != b->data[i]) return false;
        }
        return true;
    }
}

struct ArrayArray {
    int64_t type_tag;  // 4 = array of arrays
    std::vector<void*> data;  // Pointers to other arrays
};

extern "C" {
    ArrayArray* create_array_array(int64_t initial_size) {
        return new ArrayArray{4, std::vector<void*>(initial_size)};
    }

    void delete_array_array(ArrayArray* array) {
        delete array;
    }

    void* array_array_get(ArrayArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        return array->data[index];
    }

    void array_array_set(ArrayArray* array, int64_t index, void* value) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data[index] = value;
    }

    void array_array_push_back(ArrayArray* array, void* value) {
        array->data.push_back(value);
    }

    // Get the size of the array
    int64_t array_array_size(ArrayArray* array) {
        return array->data.size();
    }

    void* array_array_remove(ArrayArray* array, int64_t index) {
        if (index < 0 || index >= array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }

        auto* removed = array->data[index];
        array->data.erase(array->data.begin() + index);
        return removed;
    }

    void* array_array_pop(ArrayArray* array) {
        if (array->data.empty()) {
            throw std::out_of_range("Array is empty");
        }
        void* removed = array->data.back();
        array->data.pop_back();
        return removed;
    }

    void array_array_insert(ArrayArray* array, int64_t index, void* value) {
        if (index < 0 || index > array->data.size()) {
            throw std::out_of_range("Index out of bounds");
        }
        array->data.insert(array->data.begin() + index, value);
    }

    bool array_array_equals(ArrayArray* a, ArrayArray* b) {
        if (a->data.size() != b->data.size()) return false;
        for (size_t i = 0; i < a->data.size(); ++i) {
            void* elem_a = a->data[i];
            void* elem_b = b->data[i];
            int64_t type_tag_a = *(int64_t*)elem_a;
            int64_t type_tag_b = *(int64_t*)elem_b;
            if (type_tag_a != type_tag_b) return false;
            switch (type_tag_a) {
                case 0: // IntArray
                    if (!int_array_equals((IntArray*)elem_a, (IntArray*)elem_b)) return false;
                    break;
                case 1: // FloatArray
                    if (!float_array_equals((FloatArray*)elem_a, (FloatArray*)elem_b)) return false;
                    break;
                case 2: // BoolArray
                    if (!bool_array_equals((BoolArray*)elem_a, (BoolArray*)elem_b)) return false;
                    break;
                case 3: // StringArray
                    if (!string_array_equals((StringArray*)elem_a, (StringArray*)elem_b)) return false;
                    break;
                case 4: // ArrayArray
                    if (!array_array_equals((ArrayArray*)elem_a, (ArrayArray*)elem_b)) return false;
                    break;
                default:
                    return false;
            }
        }
        return true;
    }

    int64_t array_array_index_of(ArrayArray* array, void* value) {
        int64_t value_type_tag = *(int64_t*)value;
        for (size_t i = 0; i < array->data.size(); ++i) {
            void* elem = array->data[i];
            int64_t elem_type_tag = *(int64_t*)elem;
            if (elem_type_tag != value_type_tag) continue;
            switch (elem_type_tag) {
                case 0: // IntArray
                    if (int_array_equals((IntArray*)elem, (IntArray*)value)) return i;
                    break;
                case 1: // FloatArray
                    if (float_array_equals((FloatArray*)elem, (FloatArray*)value)) return i;
                    break;
                case 2: // BoolArray
                    if (bool_array_equals((BoolArray*)elem, (BoolArray*)value)) return i;
                    break;
                case 3: // StringArray
                    if (string_array_equals((StringArray*)elem, (StringArray*)value)) return i;
                    break;
                case 4: // ArrayArray
                    if (array_array_equals((ArrayArray*)elem, (ArrayArray*)value)) return i;
                    break;
                default:
                    break;
            }
        }
        return -1;
    }
}


extern "C" {
    int64_t alen(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0:  // IntArray
                return int_array_size((IntArray*)array_ptr);
            case 1:  // FloatArray
                return float_array_size((FloatArray*)array_ptr);
            case 2:  // BoolArray
                return bool_array_size((BoolArray*)array_ptr);
            case 3:  // StringArray
                return string_array_size((StringArray*)array_ptr);
            case 4:  // ArrayArray
                return array_array_size((ArrayArray*)array_ptr);
            default:
                throw std::invalid_argument("Unknown array type");
        }
    }

    void reverse_array(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0:  // IntArray
                std::reverse(((IntArray*)array_ptr)->data.begin(), ((IntArray*)array_ptr)->data.end());
                break;
            case 1:  // FloatArray
                std::reverse(((FloatArray*)array_ptr)->data.begin(), ((FloatArray*)array_ptr)->data.end());
                break;
            case 2:  // BoolArray
                std::reverse(((BoolArray*)array_ptr)->data.begin(), ((BoolArray*)array_ptr)->data.end());
                break;
            case 3:  // StringArray
                std::reverse(((StringArray*)array_ptr)->data.begin(), ((StringArray*)array_ptr)->data.end());
                break;
            case 4:  // ArrayArray
                std::reverse(((ArrayArray*)array_ptr)->data.begin(), ((ArrayArray*)array_ptr)->data.end());
                break;
            default:
                throw std::invalid_argument("Unknown array type");
        }
    }

    void sort_array(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0:  // IntArray
                std::sort(((IntArray*)array_ptr)->data.begin(), ((IntArray*)array_ptr)->data.end());
                break;
            case 1:  // FloatArray
                std::sort(((FloatArray*)array_ptr)->data.begin(), ((FloatArray*)array_ptr)->data.end());
                break;
            case 2:  // BoolArray
                std::sort(((BoolArray*)array_ptr)->data.begin(), ((BoolArray*)array_ptr)->data.end());
                break;
            case 3:  // StringArray
                std::sort(((StringArray*)array_ptr)->data.begin(), ((StringArray*)array_ptr)->data.end());
                break;
            default:
                throw std::invalid_argument("Sorting not supported for this array type");
        }
    }   

    void clear_array(void* array_ptr) {
        if (!array_ptr) {
            throw std::invalid_argument("Null pointer provided");
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0:  // IntArray
                ((IntArray*)array_ptr)->data.clear();
                break;
            case 1:  // FloatArray
                ((FloatArray*)array_ptr)->data.clear();
                break;
            case 2:  // BoolArray
                ((BoolArray*)array_ptr)->data.clear();
                break;
            case 3:  // StringArray
                ((StringArray*)array_ptr)->data.clear();
                break;
            case 4:  // ArrayArray
                ((ArrayArray*)array_ptr)->data.clear();
                break;
            default:
                throw std::invalid_argument("Unknown array type");
        }
    }

    void pp_array(void* array_ptr) {
        if (!array_ptr) {
            std::cout << "Null array" << std::endl;
            return;
        }
        int64_t type_tag = *(int64_t*)array_ptr;
        switch (type_tag) {
            case 0: {  // IntArray
                IntArray* arr = (IntArray*)array_ptr;
                std::cout << "[";
                for (size_t i = 0; i < arr->data.size(); ++i) {
                    std::cout << arr->data[i];
                    if (i < arr->data.size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 1: {  // FloatArray
                FloatArray* arr = (FloatArray*)array_ptr;
                std::cout << "[";
                for (size_t i = 0; i < arr->data.size(); ++i) {
                    std::cout << arr->data[i];
                    if (i < arr->data.size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 2: {  // BoolArray
                BoolArray* arr = (BoolArray*)array_ptr;
                std::cout << "[";
                for (size_t i = 0; i < arr->data.size(); ++i) {
                    std::cout << (arr->data[i] ? "true" : "false");
                    if (i < arr->data.size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 3: {  // StringArray
                StringArray* arr = (StringArray*)array_ptr;
                std::cout << "[";
                for (size_t i = 0; i < arr->data.size(); ++i) {
                    std::cout << "\"" << arr->data[i] << "\"";
                    if (i < arr->data.size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            case 4: {  // ArrayArray
                ArrayArray* arr = (ArrayArray*)array_ptr;
                std::cout << "[";
                for (size_t i = 0; i < arr->data.size(); ++i) {
                    // std::cout << arr->data[i];
                    pp_array(arr->data[i]);  // Recursively print nested arrays
                    if (i < arr->data.size() - 1) std::cout << ", ";
                }
                std::cout << "]" << std::endl;
                break;
            }
            default:
                std::cout << "Unknown array type" << std::endl;
        }
    }
}