/**
 * ============================================================
 * 文件名: cn.ts
 * 功能描述: CSS类名合并工具函数
 *          使用clsx + tailwind-merge实现类名智能合并
 *          解决Tailwind CSS类名冲突问题
 * 创建日期: 2026-06-06
 * 最后修改: 2026-06-06
 * 依赖项: clsx, tailwind-merge
 * ============================================================
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * 合并CSS类名工具函数
 * 自动解决Tailwind CSS类名冲突（如 'p-2 p-4' → 'p-4'）
 * 
 * @param inputs - 类名输入，支持字符串、对象、数组等多种格式
 * @returns 合并后的类名字符串
 * 
 * @example
 * cn('px-2 py-1', 'p-4') // → 'p-4 px-2 py-1'
 * cn({ active: isActive }, 'base-class') // → 条件类名
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
