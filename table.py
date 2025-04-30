# -*- coding: utf-8 -*-

import sys

def generate_utf8_to_sjis_table_c_code(encoding='shift_jis', max_codepoint=0xFFFF):
    print(f"// Generating table for encoding: {encoding}", file=sys.stderr)
    print(f"// Checking Unicode code points up to: 0x{max_codepoint:04X}", file=sys.stderr)

    mappings = []
    count = 0
    # 0x0000からmax_codepointまでのUnicodeコードポイントをチェック
    for i in range(max_codepoint + 1):
        char = chr(i)
        try:
            # errors='strict' でエンコードを試みる (マッピングが存在しない場合はエラー)
            sjis_bytes = char.encode(encoding, errors='strict')
            # エンコード成功かつ空でない場合 (一部の制御文字などは空になることがある)
            if sjis_bytes:
                if len(sjis_bytes) == 1:
                    # 1バイト文字のマッピングを追加
                    mappings.append(f"    {{ 0x{i:04X}, {{0x{sjis_bytes[0]:02X}, 0x00}}, 1 }}")
                elif len(sjis_bytes) == 2:
                    # 2バイト文字のマッピングを追加
                    mappings.append(f"    {{ 0x{i:04X}, {{0x{sjis_bytes[0]:02X}, 0x{sjis_bytes[1]:02X}}}, 2 }}")
                else:
                    # 通常、Shift_JISは1バイトか2バイト
                    print(f"Warning: Unexpected byte length {len(sjis_bytes)} for Unicode 0x{i:04X}", file=sys.stderr)
                count += 1
        except UnicodeEncodeError:
            # この文字は指定されたエンコーディングにマップできないため、テーブルに含めない
            pass
        except Exception as e:
            # その他の予期せぬエラー
            print(f"Error processing Unicode 0x{i:04X}: {e}", file=sys.stderr)

    print(f"// Found {count} mappings.", file=sys.stderr)

    # C言語のコードテンプレート
    c_code = """\
#ifndef UTF8_SJIS_TABLE_H
#define UTF8_SJIS_TABLE_H

#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>

// UnicodeコードポイントからShift_JISバイトへのマッピングを保持する構造体
typedef struct
{
    uint32_t unicode;      // Unicodeコードポイント
    unsigned char sjis[2]; // Shift_ｓJISバイト列(最大2バイト)
    int length;            // Shift_JISシーケンスの長さ(1または2)
} Utf8ToSjisMapping;

// 変換テーブル
const Utf8ToSjisMapping utf8_to_sjis_table[] = {
"""
    # マッピングデータを結合
    c_code += ",\n".join(mappings)
    c_code += """
};


// 変換テーブルのサイズ
const size_t utf8_to_sjis_table_size = sizeof(utf8_to_sjis_table) / sizeof(utf8_to_sjis_table[0]);

// バイナリサーチの補助関数
int compare_mappings(const void *key, const void *element)
{
    unsigned int unicode_key = *(const unsigned int *)key;
    const Utf8ToSjisMapping *mapping_element = (const Utf8ToSjisMapping *)element;
    if (unicode_key < mapping_element->unicode)
        return -1;
    if (unicode_key > mapping_element->unicode)
        return 1;
    return 0;
}

// 変換テーブルから検索する関数
const Utf8ToSjisMapping *find_sjis_mapping(unsigned int unicode_char)
{
    return (const Utf8ToSjisMapping *)bsearch(&unicode_char,
                                              utf8_to_sjis_table,
                                              utf8_to_sjis_table_size,
                                              sizeof(Utf8ToSjisMapping),
                                              compare_mappings);
}

// UTF-8からShift_JISへの変換関数
size_t utf8_to_shiftjis(const char *utf8_str, char *sjis_buffer, size_t sjis_buffer_size)
{
    size_t sjis_len = 0;
    size_t sjis_char_count = 0; // Shift_JISの文字数をカウントする変数
    const unsigned char *p = (const unsigned char *)utf8_str;
    unsigned char replacement_char = '?'; // マッピング不可能なシーケンスに使用する文字

    while (*p != '\\0')
    {
        unsigned int unicode_char = 0;
        int bytes_read = 0;

        // UTF-8 文字をデコード
        if ((*p & 0x80) == 0) // 1バイトシーケンス (ASCII)
        {
            unicode_char = *p;
            bytes_read = 1;
        }
        else if ((*p & 0xE0) == 0xC0) // 2バイトシーケンス
        {
            if ((p[1] & 0xC0) == 0x80)
            {
                unicode_char = ((p[0] & 0x1F) << 6) | (p[1] & 0x3F);
                bytes_read = 2;
            }
        }
        else if ((*p & 0xF0) == 0xE0) // 3バイトシーケンス
        {
            if ((p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80)
            {
                unicode_char = ((p[0] & 0x0F) << 12) | ((p[1] & 0x3F) << 6) | (p[2] & 0x3F);
                bytes_read = 3;
            }
        }
        else if ((*p & 0xF8) == 0xF0) // 4バイトシーケンス
        {
            if ((p[1] & 0xC0) == 0x80 && (p[2] & 0xC0) == 0x80 && (p[3] & 0xC0) == 0x80)
            {
                unicode_char = ((p[0] & 0x07) << 18) | ((p[1] & 0x3F) << 12) | ((p[2] & 0x3F) << 6) | (p[3] & 0x3F);
                bytes_read = 4;
            }
        }

        if (bytes_read == 0)
        {
            // 無効な UTF-8 シーケンス、'?' で置換
            if (sjis_len + 1 >= sjis_buffer_size)
                return (size_t)-1; // バッファオーバーフロー
            sjis_buffer[sjis_len++] = replacement_char;
            sjis_char_count++; // 置換文字をカウント
            p++;               // 無効なバイトをスキップ
            continue;
        }

        // デコードされた Unicode 文字のマッピングを検索
        const Utf8ToSjisMapping *mapping = find_sjis_mapping(unicode_char);

        if (mapping)
        {
            // マッピングが見つかった場合
            if (sjis_len + mapping->length >= sjis_buffer_size)
                return (size_t)-1; // バッファオーバーフロー
            memcpy(sjis_buffer + sjis_len, mapping->sjis, mapping->length);
            sjis_len += mapping->length;
            sjis_char_count++; // マッピングされた文字をカウント
        }
        else
        {
            // 文字がテーブルにないか、ASCII 文字です
            if (sjis_len + 1 >= sjis_buffer_size)
                return (size_t)-1; // 1バイト文字のバッファオーバーフロー

            if (unicode_char <= 0x7F)
            { // ASCII 文字をそのまま通す
                sjis_buffer[sjis_len++] = (char)unicode_char;
            }
            else
            { // マッピング不可かつ非 ASCII 文字を '?' で置換
                sjis_buffer[sjis_len++] = replacement_char;
            }
            sjis_char_count++; // ASCII 文字または置換文字をカウント
        }
        p += bytes_read; // 次の UTF-8 文字へ移動
    }

    // スペースがあれば Shift_JIS 文字列をヌル終端する
    if (sjis_len < sjis_buffer_size)
    {
        sjis_buffer[sjis_len] = '\\0';
    }
    else
    {
        // ヌル終端文字のためのスペースがない、切り捨ての可能性を示す
        // オーバーフロー前に正常に書き込まれた文字数を返す
    }

    return sjis_char_count; // 文字数を返す
}

#endif
"""
    return c_code

if __name__ == "__main__":
    # Windows環境などでより互換性の高いテーブルが必要な場合は encoding='cp932' を試す
    # max_codepointで、チェックするUnicodeの範囲を変更可能
    c_table_code = generate_utf8_to_sjis_table_c_code(encoding='shift_jis', max_codepoint=0xFFFF)
    with open("utf8_to_sjis_table.h", "w", encoding="utf-8") as f:
        f.write(c_table_code)
    print(f"Table saved to utf8_to_sjis_table.h", file=sys.stderr)
