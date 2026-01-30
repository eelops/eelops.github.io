---
title: 从 equals() 理解 Java 的运行机制、JVM 与类型转换
author: eelops
date: 2026-01-25 14:00:00 +0800
categories: [Java面向对象基础, 方法重写]
tags: [Java面向对象基础]
---

## 一、问题背景：我到底在疑惑什么？

在学习 Java 重写方法时，我遇到了这样几个问题：

1. Java 在运行过程中是不是“已经定性了”要调用哪个方法？
2. Java 既是编译型语言，又是解释型语言，这和不同方法的调用的调用有关吗？
3. `this.name.equals(person.name)` 到底调用的是谁的 `equals`？
4. 既然已经定义好了用哪个 `equals`，那如果中途**强制类型转换**会怎么样？
5. 这些行为是不是和 JVM 有关系？

为了搞清楚这些问题，我们以如下代码为核心进行分析。

## 二、实战代码：Person.equals 的完整示例

```java
public class Person {

    private String name;
    private int age;
    private String sex;

    @Override
    public boolean equals(Object obj) {
        if (obj == null) return false;

        if (obj instanceof Person) {
            Person person = (Person) obj;
            return this.name.equals(person.name)
                    && this.age == person.age
                    && this.sex.equals(person.sex);
        }
        return false;
    }
}
```

---

## 三、这段代码“表面上”在做什么？

从初学者角度看，这段代码的逻辑其实很清晰：

> **两个 Person 对象是否相等，取决于它们的 name、age、sex 是否全部相同。**

但真正让我困惑的是：

> **Java 是如何在运行时，准确地知道要调用哪一个 `equals` 方法的？**

---

## 四、Java 是编译型语言，还是解释型语言？

### 结论

✅ **Java 是“编译 + 运行时解释 / 动态执行”的混合模型**

执行流程如下：

```
.java 源码
   ↓ javac
.class 字节码
   ↓ JVM
运行（解释执行 / JIT 编译）
```

### 这意味着什么？

- **编译期**：
  Java 只做一件事 —— **检查语法和类型是否合理**
- **运行期（JVM）**：
  才真正决定：
  - 调用哪个方法
  - 使用哪个类的实现

✅ **方法最终“用谁的实现”，不是在编译期决定的，而是在运行期由 JVM 决定的**

---

## 五、回到代码：`this.name.equals(person.name)` 到底发生了什么？

### 1️⃣ 编译期在做什么？

```java
this.name.equals(person.name);
```

编译器看到：

- `this.name` 的**声明类型**是 `String`
- `String` 是否有 `equals(Object)` 方法？

✅ 有
✅ 编译通过

❗**注意**：
此时**并没有决定调用哪个具体实现**。

---

### 2️⃣ 运行期（JVM）在做什么？

运行时，JVM 会去看：

```java
this.name 实际指向的对象是什么？
```

例如：

```java
this.name = new String("Tom");
```

JVM 的判断是：

> 真实对象是 `String`，
> 所以调用 `String.equals(Object)`。

✅ **这是 JVM 的“动态绑定（Dynamic Dispatch）机制”**

---

## 六、为什么不会调用 Person.equals？

这是一个非常容易误解的点。

```java
this.name.equals(person.name);
```

- 调用者是 `this.name`
- `this.name` 是一个 **String 对象**
- 所以：
  - 调用的是 **String.equals**
  - 和 `Person.equals` 完全无关

✅ **方法属于对象，而不是写代码的类**

---

## 七、如果中途发生“强制类型转换”会怎么样？

这是我最担心的问题之一。

---

### 情况 1：向上转型（子类 → 父类）

```java
Object o = this.name;
o.equals(person.name);
```

✅ 仍然调用 `String.equals`

原因：

- 强转只改变**变量的类型**
- 不改变**对象的真实类型**

---

### 情况 2：向下转型（父类 → 子类）

```java
Object o = "Tom";
String s = (String) o;
s.equals("Tom");
```

✅ 正常运行
✅ 调用 `String.equals`

---

### 情况 3：错误的强制转换

```java
Object o = "Tom";
Person p = (Person) o; // ❌
```

❌ **运行期抛出 ClassCastException**

JVM 会检查：

> “这个对象是不是 Person？”
> 不是 → 直接报错

---

### ✅ 关键结论

> **强制类型转换永远不会改变 equals 的实现**
> **方法调用始终由“对象的真实类型”决定**

---

## 八、这一切和 JVM 有什么关系？


JVM 内部使用一种机制（虚方法表）：

```
对象 → 找到所属类 → 查方法表 → 调用对应实现
```

所以：

- `this.name` 是 String 对象
- JVM 查 String 的方法表
- 找到 String.equals
- 执行

---


## 九、再回头看 Person.equals 这段代码

```java
if (obj instanceof Person) {
    Person person = (Person) obj;
    return this.name.equals(person.name)
            && this.age == person.age
            && this.sex.equals(person.sex);
}
```

这段代码体现了 Java 的几个核心思想：

1. **编译期只保证安全**
2. **运行期由 JVM 决定行为**
3. **instanceof + 强转 是运行期类型控制的标准方式**
4. **equals 的真正实现，取决于属性对象本身**

## 方法重写的本质：

- 子类在继承父类后，
- 用自己的实现替换父类的实现，
- 并且在运行期由对象的真实类型决定调用哪个方法。

所以我们也可以得知`static`方法不能被重写



