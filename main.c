#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "utf8_to_sjis_table.h"

int main()
{
    const char *utf8_input = "テスト① AΑαあ阿"; // UTF-8 入力文字列
    char sjis_output[100];                  // Shift_JIS 出力バッファ
    size_t output_char_count;               // 出力文字数
    size_t output_byte_len;                 // バイト長も取得したい場合は別途計算が必要

    printf("UTF-8 Input: %s\n", utf8_input);

    output_char_count = utf8_to_shiftjis(utf8_input, sjis_output, sizeof(sjis_output));

    if (output_char_count != (size_t)-1)
    {
        output_byte_len = strlen(sjis_output);

        printf("Shift_JIS Output (chars: %zu, bytes: %zu): ", output_char_count, output_byte_len);
        for (size_t i = 0; i < output_byte_len; ++i)
        {
            printf("0x%02X ", (unsigned char)sjis_output[i]);
        }
        printf("\n");
    }
    else
    {
        printf("Conversion failed (buffer too small or invalid UTF-8).\n");
    }

    return 0;
}