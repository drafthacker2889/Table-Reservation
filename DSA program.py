#!/usr/bin/env python
# coding: utf-8

# In[2]:


seatlist = {}
print("\t\t\t\t\t\t WELCOME TO RESTAURANT\n")
def print_menu():
    print (30 * "-" , "Menu", 30 * "-")
    print ("1. Add reservation")
    print ("2 Remove reservation")
    print ("3 print seat reservation list")
    print ("4 exit")
    print (67 * "-")
loop=True

while loop:
    print_menu()
    choice = input("Enter your choice [1-4]: ")
    choice=int(choice)
    if choice == 1:
        seat = input("Which Seat?: ")
        if seat in seatlist:
            print (67 * "-")
            print("OCCUPIED")
            print (67 * "-")
        else:
            name = input("What name?:  ")
            seatlist.update({seat:name})
    elif choice == 2:
        seat= input("ok, which seat to remove?:  ")
        seatlist.pop(seat)
        print("seat no",choice,"is available again")
    elif choice == 3:
        print(seatlist)
    elif choice == 4:
        print("thank you")
        loop=False
    else:
        print("invalid option!")

        


# In[ ]:




